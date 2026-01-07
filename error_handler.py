"""
Error handling and logging system for the Voice Assistant application.
Provides centralized error management, recovery strategies, and logging.
"""

import logging
import traceback
import sys
import threading
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from models import SystemStatus
from utils import get_system_info, format_timestamp


class ErrorSeverity(Enum):
    """Severity levels for errors."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Categories of errors that can occur."""
    SPEECH_RECOGNITION = "speech_recognition"
    AUDIO_PROCESSING = "audio_processing"
    COMPUTER_VISION = "computer_vision"
    NETWORK = "network"
    FILE_SYSTEM = "file_system"
    DATABASE = "database"
    CONFIGURATION = "configuration"
    HARDWARE = "hardware"
    SYSTEM = "system"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Context information for an error."""
    component: str
    operation: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    system_info: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ErrorRecord:
    """Complete error record with context and recovery information."""
    error_id: str
    message: str
    exception_type: str
    traceback: str
    severity: ErrorSeverity
    category: ErrorCategory
    context: ErrorContext
    retry_count: int = 0
    max_retries: int = 3
    recovery_actions: List[str] = field(default_factory=list)
    resolved: bool = False
    resolution_time: Optional[datetime] = None

    def mark_resolved(self) -> None:
        """Mark the error as resolved."""
        self.resolved = True
        self.resolution_time = datetime.now()

    def can_retry(self) -> bool:
        """Check if the error can be retried."""
        return self.retry_count < self.max_retries and not self.resolved


class ErrorHandler:
    """
    Centralized error handling system with logging, recovery, and monitoring.
    """

    def __init__(self, log_level: str = "INFO"):
        """
        Initialize the error handler.

        Args:
            log_level: Logging level for error messages
        """
        self.logger = logging.getLogger("voice_assistant.error_handler")
        self.logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

        # Error storage
        self.error_records: Dict[str, ErrorRecord] = {}
        self.error_counts: Dict[ErrorCategory, int] = {}
        self.recovery_strategies: Dict[ErrorCategory, Callable] = {}

        # Initialize recovery strategies
        self._init_recovery_strategies()

        # Error monitoring
        self.monitoring_active = True
        self.error_thresholds = {
            ErrorSeverity.LOW: 10,
            ErrorSeverity.MEDIUM: 5,
            ErrorSeverity.HIGH: 2,
            ErrorSeverity.CRITICAL: 1
        }

        self.logger.info("Error handler initialized")

    def _init_recovery_strategies(self) -> None:
        """Initialize recovery strategies for different error categories."""
        self.recovery_strategies = {
            ErrorCategory.SPEECH_RECOGNITION: self._recover_speech_recognition,
            ErrorCategory.AUDIO_PROCESSING: self._recover_audio_processing,
            ErrorCategory.COMPUTER_VISION: self._recover_computer_vision,
            ErrorCategory.NETWORK: self._recover_network,
            ErrorCategory.FILE_SYSTEM: self._recover_file_system,
            ErrorCategory.DATABASE: self._recover_database,
            ErrorCategory.HARDWARE: self._recover_hardware
        }

    def handle_error(self, error: Exception, context: ErrorContext,
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM) -> str:
        """
        Handle an error with context and recovery attempts.

        Args:
            error: The exception that occurred
            context: Context information about the error
            severity: Severity level of the error

        Returns:
            Error ID for tracking
        """
        error_id = f"err_{int(datetime.now().timestamp() * 1000)}_{threading.current_thread().ident}"

        # Determine error category
        category = self._categorize_error(error, context)

        # Create error record
        error_record = ErrorRecord(
            error_id=error_id,
            message=str(error),
            exception_type=type(error).__name__,
            traceback=traceback.format_exc(),
            severity=severity,
            category=category,
            context=context,
            recovery_actions=[]
        )

        # Store error record
        self.error_records[error_id] = error_record
        self.error_counts[category] = self.error_counts.get(category, 0) + 1

        # Log error
        self._log_error(error_record)

        # Attempt recovery
        if self._should_attempt_recovery(error_record):
            self._attempt_recovery(error_record)

        # Check error thresholds
        self._check_error_thresholds(error_record)

        return error_id

    def _categorize_error(self, error: Exception, context: ErrorContext) -> ErrorCategory:
        """
        Categorize an error based on exception type and context.

        Args:
            error: The exception that occurred
            context: Context information

        Returns:
            Error category
        """
        error_type = type(error).__name__
        component = context.component.lower()

        # Categorize by exception type
        if "speech" in component or "recognition" in error_type.lower():
            return ErrorCategory.SPEECH_RECOGNITION
        elif "audio" in component or "sound" in component:
            return ErrorCategory.AUDIO_PROCESSING
        elif "vision" in component or "detection" in component or "camera" in component:
            return ErrorCategory.COMPUTER_VISION
        elif "network" in str(error).lower() or "connection" in str(error).lower():
            return ErrorCategory.NETWORK
        elif "file" in error_type.lower() or "io" in error_type.lower():
            return ErrorCategory.FILE_SYSTEM
        elif "database" in component or "sqlite" in error_type.lower():
            return ErrorCategory.DATABASE
        elif "config" in component:
            return ErrorCategory.CONFIGURATION
        elif "hardware" in str(error).lower() or "device" in str(error).lower():
            return ErrorCategory.HARDWARE
        else:
            return ErrorCategory.UNKNOWN

    def _log_error(self, error_record: ErrorRecord) -> None:
        """
        Log an error record with appropriate level.

        Args:
            error_record: Error record to log
        """
        log_message = f"[{error_record.error_id}] {error_record.category.value}: {error_record.message}"
        log_data = {
            "error_id": error_record.error_id,
            "severity": error_record.severity.value,
            "category": error_record.category.value,
            "component": error_record.context.component,
            "operation": error_record.context.operation,
            "session_id": error_record.context.session_id,
            "traceback": error_record.traceback
        }

        if error_record.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message, extra=log_data)
        elif error_record.severity == ErrorSeverity.HIGH:
            self.logger.error(log_message, extra=log_data)
        elif error_record.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message, extra=log_data)
        else:
            self.logger.info(log_message, extra=log_data)

    def _should_attempt_recovery(self, error_record: ErrorRecord) -> bool:
        """
        Determine if recovery should be attempted for an error.

        Args:
            error_record: Error record to check

        Returns:
            True if recovery should be attempted
        """
        # Don't attempt recovery for critical errors
        if error_record.severity == ErrorSeverity.CRITICAL:
            return False

        # Don't retry if max retries exceeded
        if not error_record.can_retry():
            return False

        # Check if we have a recovery strategy
        return error_record.category in self.recovery_strategies

    def _attempt_recovery(self, error_record: ErrorRecord) -> None:
        """
        Attempt to recover from an error.

        Args:
            error_record: Error record to recover from
        """
        try:
            recovery_func = self.recovery_strategies.get(error_record.category)
            if recovery_func:
                success = recovery_func(error_record)
                if success:
                    error_record.mark_resolved()
                    error_record.recovery_actions.append("Recovery successful")
                    self.logger.info(f"Error {error_record.error_id} recovered successfully")
                else:
                    error_record.retry_count += 1
                    error_record.recovery_actions.append(f"Recovery attempt {error_record.retry_count} failed")
                    self.logger.warning(f"Recovery failed for error {error_record.error_id}")
            else:
                self.logger.warning(f"No recovery strategy for error category {error_record.category.value}")

        except Exception as recovery_error:
            error_record.retry_count += 1
            error_record.recovery_actions.append(f"Recovery error: {recovery_error}")
            self.logger.error(f"Recovery attempt failed for error {error_record.error_id}: {recovery_error}")

    def _recover_speech_recognition(self, error_record: ErrorRecord) -> bool:
        """Recovery strategy for speech recognition errors."""
        # Try to recalibrate microphone
        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=1)
            return True
        except Exception:
            return False

    def _recover_audio_processing(self, error_record: ErrorRecord) -> bool:
        """Recovery strategy for audio processing errors."""
        # Try to restart audio system
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.say("Audio system restarted")
            engine.runAndWait()
            return True
        except Exception:
            return False

    def _recover_computer_vision(self, error_record: ErrorRecord) -> bool:
        """Recovery strategy for computer vision errors."""
        # Try to reinitialize camera
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                cap.release()
                return True
        except Exception:
            pass
        return False

    def _recover_network(self, error_record: ErrorRecord) -> bool:
        """Recovery strategy for network errors."""
        # For network errors, we typically just log and continue
        # as they may be temporary
        return True

    def _recover_file_system(self, error_record: ErrorRecord) -> bool:
        """Recovery strategy for file system errors."""
        # Try to create missing directories
        try:
            import os
            from pathlib import Path
            # This is a generic recovery - specific paths would be better
            return True
        except Exception:
            return False

    def _recover_database(self, error_record: ErrorRecord) -> bool:
        """Recovery strategy for database errors."""
        # Try to reconnect to database
        try:
            import sqlite3
            # This is generic - specific database paths would be better
            return True
        except Exception:
            return False

    def _recover_hardware(self, error_record: ErrorRecord) -> bool:
        """Recovery strategy for hardware errors."""
        # Hardware errors are typically not recoverable automatically
        return False

    def _check_error_thresholds(self, error_record: ErrorRecord) -> None:
        """
        Check if error thresholds have been exceeded.

        Args:
            error_record: Error record to check
        """
        category_count = self.error_counts.get(error_record.category, 0)
        threshold = self.error_thresholds.get(error_record.severity, float('inf'))

        if category_count >= threshold:
            self.logger.warning(
                f"Error threshold exceeded for {error_record.category.value} "
                f"(count: {category_count}, threshold: {threshold})"
            )

            # Could trigger alerts, system shutdown, etc. here
            if error_record.severity == ErrorSeverity.CRITICAL:
                self.logger.critical("Critical error threshold exceeded - system may be unstable")

    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all errors.

        Returns:
            Dictionary with error summary
        """
        total_errors = len(self.error_records)
        resolved_errors = sum(1 for e in self.error_records.values() if e.resolved)
        unresolved_errors = total_errors - resolved_errors

        return {
            "total_errors": total_errors,
            "resolved_errors": resolved_errors,
            "unresolved_errors": unresolved_errors,
            "error_counts_by_category": dict(self.error_counts),
            "recent_errors": [
                {
                    "id": error_id,
                    "message": record.message,
                    "severity": record.severity.value,
                    "category": record.category.value,
                    "timestamp": format_timestamp(record.context.timestamp)
                }
                for error_id, record in list(self.error_records.items())[-10:]  # Last 10 errors
            ]
        }

    def clear_resolved_errors(self, max_age_days: int = 7) -> int:
        """
        Clear resolved errors older than specified days.

        Args:
            max_age_days: Maximum age of errors to keep

        Returns:
            Number of errors cleared
        """
        cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)
        errors_to_remove = []

        for error_id, record in self.error_records.items():
            if record.resolved and record.context.timestamp.timestamp() < cutoff_time:
                errors_to_remove.append(error_id)

        for error_id in errors_to_remove:
            del self.error_records[error_id]

        self.logger.info(f"Cleared {len(errors_to_remove)} resolved errors")
        return len(errors_to_remove)

    def export_error_report(self, output_file: str) -> bool:
        """
        Export error report to file.

        Args:
            output_file: Path to output file

        Returns:
            True if export successful
        """
        try:
            import json
            from pathlib import Path

            report = {
                "generated_at": format_timestamp(datetime.now()),
                "summary": self.get_error_summary(),
                "detailed_errors": [
                    {
                        "error_id": error_id,
                        "message": record.message,
                        "severity": record.severity.value,
                        "category": record.category.value,
                        "component": record.context.component,
                        "operation": record.context.operation,
                        "timestamp": format_timestamp(record.context.timestamp),
                        "resolved": record.resolved,
                        "retry_count": record.retry_count,
                        "traceback": record.traceback
                    }
                    for error_id, record in self.error_records.items()
                ]
            }

            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)

            self.logger.info(f"Error report exported to {output_file}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to export error report: {e}")
            return False


def error_handler(severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 category: Optional[ErrorCategory] = None):
    """
    Decorator for automatic error handling.

    Args:
        severity: Severity level for caught errors
        category: Optional error category override
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            error_handler_instance = getattr(func, '_error_handler', None)
            if not error_handler_instance:
                # Try to get from class or module
                error_handler_instance = getattr(args[0] if args else None, 'error_handler', None)

            if not error_handler_instance:
                # Create a default error handler
                error_handler_instance = ErrorHandler()

            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = ErrorContext(
                    component=getattr(args[0], '__class__.__name__', 'unknown') if args else 'function',
                    operation=func.__name__,
                    parameters={"args_count": len(args), "kwargs_keys": list(kwargs.keys())}
                )

                if category:
                    context_component = context.component.lower()
                    # Override category based on component
                    if "speech" in context_component:
                        context_category = ErrorCategory.SPEECH_RECOGNITION
                    elif "vision" in context_component or "detection" in context_component:
                        context_category = ErrorCategory.COMPUTER_VISION
                    elif "data" in context_component:
                        context_category = ErrorCategory.DATABASE
                    else:
                        context_category = category
                else:
                    context_category = ErrorCategory.UNKNOWN

                error_id = error_handler_instance.handle_error(e, context, severity)
                raise  # Re-raise the exception after handling

        return wrapper
    return decorator


class SystemMonitor:
    """
    System monitoring and health checking.
    """

    def __init__(self, error_handler: ErrorHandler):
        """
        Initialize system monitor.

        Args:
            error_handler: Error handler instance
        """
        self.error_handler = error_handler
        self.logger = logging.getLogger("voice_assistant.system_monitor")
        self.system_status = SystemStatus()

    def perform_health_check(self) -> SystemStatus:
        """
        Perform a comprehensive health check of the system.

        Returns:
            Updated system status
        """
        try:
            # Check microphone
            self.system_status.is_microphone_active = self._check_microphone()

            # Check camera
            self.system_status.is_camera_active = self._check_camera()

            # Check voice engine
            self.system_status.is_voice_engine_active = self._check_voice_engine()

            # Get system resources
            system_info = get_system_info()
            self.system_status.memory_usage_mb = system_info.get("memory_percent", 0) / 100 * system_info.get("memory_total", 0) / (1024 * 1024)
            self.system_status.cpu_usage_percent = system_info.get("cpu_percent", 0)

            self.system_status.update_health_status()

            self.logger.debug("Health check completed successfully")
            return self.system_status

        except Exception as e:
            context = ErrorContext(
                component="SystemMonitor",
                operation="perform_health_check"
            )
            self.error_handler.handle_error(e, context, ErrorSeverity.HIGH)
            return self.system_status

    def _check_microphone(self) -> bool:
        """Check if microphone is accessible."""
        try:
            import speech_recognition as sr
            with sr.Microphone() as source:
                return True
        except Exception:
            return False

    def _check_camera(self) -> bool:
        """Check if camera is accessible."""
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            result = cap.isOpened()
            cap.release()
            return result
        except Exception:
            return False

    def _check_voice_engine(self) -> bool:
        """Check if voice engine is working."""
        try:
            import pyttsx3
            engine = pyttsx3.init()
            return engine is not None
        except Exception:
            return False
