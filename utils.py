"""
Utility functions and helpers for the Voice Assistant application.
This module contains common functions used across different parts of the system.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import psutil
import platform
from functools import wraps
import time


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    Setup logging configuration for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("voice_assistant")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Could not create log file {log_file}: {e}")

    return logger


def get_system_info() -> Dict[str, Any]:
    """
    Get comprehensive system information.

    Returns:
        Dictionary containing system information
    """
    try:
        return {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_total": psutil.virtual_memory().total,
            "memory_available": psutil.virtual_memory().available,
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "error": f"Could not get system info: {e}",
            "timestamp": datetime.now().isoformat()
        }


def load_config_from_file(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from a JSON file.

    Args:
        config_path: Path to the configuration file

    Returns:
        Configuration dictionary

    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If config file is not valid JSON
    """
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_file, 'r') as f:
        return json.load(f)


def save_config_to_file(config: Dict[str, Any], config_path: str) -> None:
    """
    Save configuration to a JSON file.

    Args:
        config: Configuration dictionary to save
        config_path: Path where to save the configuration
    """
    config_file = Path(config_path)
    config_file.parent.mkdir(parents=True, exist_ok=True)

    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)


def timing_decorator(func):
    """
    Decorator to measure and log function execution time.

    Args:
        func: Function to decorate

    Returns:
        Decorated function that logs execution time
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        logger = logging.getLogger("voice_assistant.utils")
        logger.debug(f"Starting execution of {func.__name__}")

        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(".2f")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(".2f")
            raise

    return wrapper


def safe_file_operation(operation_func):
    """
    Decorator for safe file operations with error handling.

    Args:
        operation_func: Function that performs file operations

    Returns:
        Decorated function with error handling
    """
    @wraps(operation_func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger("voice_assistant.utils")
        try:
            return operation_func(*args, **kwargs)
        except FileNotFoundError as e:
            logger.error(f"File not found: {e}")
            raise
        except PermissionError as e:
            logger.error(f"Permission denied: {e}")
            raise
        except IOError as e:
            logger.error(f"IO error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in file operation: {e}")
            raise

    return wrapper


def validate_file_path(file_path: str, must_exist: bool = False) -> bool:
    """
    Validate if a file path is valid and optionally check if it exists.

    Args:
        file_path: Path to validate
        must_exist: Whether the file must exist

    Returns:
        True if path is valid, False otherwise
    """
    try:
        path = Path(file_path)
        if must_exist:
            return path.exists()
        else:
            # Check if the parent directory exists and is writable
            return path.parent.exists() and os.access(path.parent, os.W_OK)
    except Exception:
        return False


def format_timestamp(timestamp: datetime) -> str:
    """
    Format a datetime object to a readable string.

    Args:
        timestamp: Datetime object to format

    Returns:
        Formatted timestamp string
    """
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")


def calculate_confidence_score(raw_confidence: float, threshold: float = 0.5) -> float:
    """
    Calculate normalized confidence score.

    Args:
        raw_confidence: Raw confidence value (typically 0-1)
        threshold: Minimum threshold for valid detection

    Returns:
        Normalized confidence score (0-100)
    """
    if raw_confidence < threshold:
        return 0.0

    # Normalize to 0-100 scale
    normalized = ((raw_confidence - threshold) / (1.0 - threshold)) * 100
    return max(0.0, min(100.0, normalized))


def create_session_id() -> str:
    """
    Create a unique session identifier.

    Returns:
        Unique session ID string
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_suffix = str(hash(datetime.now()))[-6:]
    return f"session_{timestamp}_{random_suffix}"


def parse_voice_command(command_text: str) -> Dict[str, Any]:
    """
    Parse voice command text to extract structured information.

    Args:
        command_text: Raw voice command text

    Returns:
        Dictionary with parsed command information
    """
    text = command_text.lower().strip()

    # Simple keyword-based parsing (could be enhanced with NLP)
    parsed = {
        "original_text": command_text,
        "action": None,
        "target": None,
        "parameters": {}
    }

    # Define command patterns
    command_patterns = {
        "search": ["search", "find", "look up"],
        "play": ["play", "start", "begin"],
        "open": ["open", "launch", "start"],
        "show": ["show", "display", "tell me"],
        "detect": ["detect", "scan", "identify"]
    }

    # Check for action keywords
    for action, keywords in command_patterns.items():
        if any(keyword in text for keyword in keywords):
            parsed["action"] = action
            break

    # Extract specific targets
    if "youtube" in text:
        parsed["target"] = "youtube"
    elif "google" in text:
        parsed["target"] = "google"
    elif "wikipedia" in text:
        parsed["target"] = "wikipedia"
    elif "camera" in text:
        parsed["target"] = "camera"
    elif "money" in text or "rupee" in text:
        parsed["target"] = "money"
    elif "object" in text:
        parsed["target"] = "object"

    return parsed


def get_memory_usage() -> Dict[str, float]:
    """
    Get current memory usage statistics.

    Returns:
        Dictionary with memory usage information
    """
    try:
        memory = psutil.virtual_memory()
        return {
            "total_mb": memory.total / (1024 * 1024),
            "available_mb": memory.available / (1024 * 1024),
            "used_mb": memory.used / (1024 * 1024),
            "percent": memory.percent
        }
    except Exception:
        return {"error": "Could not get memory usage"}


def cleanup_temp_files(temp_dir: str = "temp", max_age_hours: int = 24) -> int:
    """
    Clean up temporary files older than specified age.

    Args:
        temp_dir: Directory containing temporary files
        max_age_hours: Maximum age of files to keep (in hours)

    Returns:
        Number of files cleaned up
    """
    logger = logging.getLogger("voice_assistant.utils")
    temp_path = Path(temp_dir)
    if not temp_path.exists():
        return 0

    cleaned_count = 0
    cutoff_time = time.time() - (max_age_hours * 3600)

    try:
        for file_path in temp_path.glob("*"):
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                file_path.unlink()
                cleaned_count += 1
                logger.debug(f"Cleaned up temp file: {file_path}")

    except Exception as e:
        logger.error(f"Error during temp file cleanup: {e}")

    return cleaned_count
