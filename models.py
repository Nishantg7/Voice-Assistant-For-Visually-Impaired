"""
Data models and configuration classes for the Voice Assistant application.
This module defines the core data structures used throughout the system.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class DetectionConfidence(Enum):
    """Enumeration for detection confidence levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class VoiceCommandType(Enum):
    """Types of voice commands supported by the assistant."""
    WIKIPEDIA_SEARCH = "wikipedia_search"
    YOUTUBE_SEARCH = "youtube_search"
    YOUTUBE_PLAY = "youtube_play"
    WEB_BROWSER = "web_browser"
    TIME_QUERY = "time_query"
    JOKE = "joke"
    CAMERA_CONTROL = "camera_control"
    MONEY_DETECTION = "money_detection"
    OBJECT_DETECTION = "object_detection"
    SYSTEM_CONTROL = "system_control"


@dataclass
class VoiceCommand:
    """Represents a parsed voice command."""
    command_type: VoiceCommandType
    raw_text: str
    parsed_parameters: Dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class DetectionResult:
    """Result from object or money detection."""
    object_class: str
    confidence: float
    bounding_box: Optional[tuple] = None  # (x1, y1, x2, y2)
    timestamp: datetime = field(default_factory=datetime.now)

    def get_confidence_level(self) -> DetectionConfidence:
        """Get confidence level based on confidence score."""
        if self.confidence >= 0.8:
            return DetectionConfidence.HIGH
        elif self.confidence >= 0.5:
            return DetectionConfidence.MEDIUM
        else:
            return DetectionConfidence.LOW


@dataclass
class SessionData:
    """Data for a voice assistant session."""
    session_id: str
    start_time: datetime = field(default_factory=datetime.now)
    commands_processed: List[VoiceCommand] = field(default_factory=list)
    detections_made: List[DetectionResult] = field(default_factory=list)
    is_active: bool = True
    total_duration: float = 0.0

    def add_command(self, command: VoiceCommand) -> None:
        """Add a command to the session."""
        self.commands_processed.append(command)

    def add_detection(self, detection: DetectionResult) -> None:
        """Add a detection to the session."""
        self.detections_made.append(detection)

    def end_session(self) -> None:
        """End the session and calculate duration."""
        if self.is_active:
            self.is_active = False
            self.total_duration = (datetime.now() - self.start_time).total_seconds()


@dataclass
class AppConfig:
    """Application configuration settings."""
    voice_engine: str = "sapi5"
    voice_rate: int = 200
    voice_volume: float = 0.8
    recognition_language: str = "en-in"
    camera_index: int = 0
    detection_threshold: float = 0.5
    max_session_duration: int = 3600  # seconds
    enable_logging: bool = True
    log_level: str = "INFO"

    # Model configurations
    object_detection_model: str = "object_detection.pt"
    money_detection_model: str = "rupee.pt"

    # Class names for detection
    object_classes: List[str] = field(default_factory=lambda: [
        'book', 'car', 'cell phone', 'chair', 'cup', 'glasses',
        'laptop', 'pen', 'person', 'plant', 'screen'
    ])

    money_classes: List[str] = field(default_factory=lambda: [
        '10', '100', '20', '200', '2000', '50', '500'
    ])


@dataclass
class AudioConfig:
    """Audio processing configuration."""
    sample_rate: int = 44100
    channels: int = 1
    chunk_size: int = 1024
    pause_threshold: float = 0.5
    energy_threshold: int = 300
    dynamic_energy_threshold: bool = True


@dataclass
class ProcessingStats:
    """Statistics for processing operations."""
    total_commands: int = 0
    successful_commands: int = 0
    failed_commands: int = 0
    total_detections: int = 0
    average_processing_time: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)

    def update_command_stats(self, success: bool, processing_time: float) -> None:
        """Update command processing statistics."""
        self.total_commands += 1
        if success:
            self.successful_commands += 1
        else:
            self.failed_commands += 1

        # Update rolling average
        if self.total_commands == 1:
            self.average_processing_time = processing_time
        else:
            self.average_processing_time = (
                (self.average_processing_time * (self.total_commands - 1) + processing_time)
                / self.total_commands
            )
        self.last_updated = datetime.now()

    def get_success_rate(self) -> float:
        """Get command success rate as percentage."""
        if self.total_commands == 0:
            return 0.0
        return (self.successful_commands / self.total_commands) * 100


@dataclass
class SystemStatus:
    """Current system status information."""
    is_voice_engine_active: bool = False
    is_camera_active: bool = False
    is_microphone_active: bool = False
    active_sessions: int = 0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    last_health_check: datetime = field(default_factory=datetime.now)

    def update_health_status(self) -> None:
        """Update the last health check timestamp."""
        self.last_health_check = datetime.now()

    def is_system_healthy(self) -> bool:
        """Check if the system is in a healthy state."""
        # Consider system healthy if last health check was within 30 seconds
        time_since_check = (datetime.now() - self.last_health_check).total_seconds()
        return time_since_check < 30
