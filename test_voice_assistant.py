"""
Unit tests for the Voice Assistant application components.
Tests models, utilities, speech processing, data management, and error handling.
"""

import unittest
import tempfile
import os
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Import our modules
from models import (
    VoiceCommand, VoiceCommandType, DetectionResult, DetectionConfidence,
    SessionData, AppConfig, AudioConfig, ProcessingStats, SystemStatus
)
from utils import (
    setup_logging, get_system_info, load_config_from_file, save_config_to_file,
    timing_decorator, validate_file_path, format_timestamp, parse_voice_command,
    create_session_id
)
from speech_processor import SpeechProcessor, TextToSpeechEngine
from data_manager import DataManager
from error_handler import ErrorHandler, ErrorSeverity, ErrorCategory, ErrorContext, SystemMonitor


class TestModels(unittest.TestCase):
    """Test cases for data models."""

    def test_voice_command_creation(self):
        """Test VoiceCommand creation and properties."""
        command = VoiceCommand(
            command_type=VoiceCommandType.WIKIPEDIA_SEARCH,
            raw_text="search wikipedia for python",
            confidence_score=0.85
        )

        self.assertEqual(command.command_type, VoiceCommandType.WIKIPEDIA_SEARCH)
        self.assertEqual(command.raw_text, "search wikipedia for python")
        self.assertEqual(command.confidence_score, 0.85)
        self.assertIsInstance(command.timestamp, datetime)

    def test_detection_result_confidence(self):
        """Test DetectionResult confidence level calculation."""
        high_conf = DetectionResult("person", 0.9)
        med_conf = DetectionResult("car", 0.6)
        low_conf = DetectionResult("book", 0.3)

        self.assertEqual(high_conf.get_confidence_level(), DetectionConfidence.HIGH)
        self.assertEqual(med_conf.get_confidence_level(), DetectionConfidence.MEDIUM)
        self.assertEqual(low_conf.get_confidence_level(), DetectionConfidence.LOW)

    def test_session_data_operations(self):
        """Test SessionData operations."""
        session = SessionData("test_session")

        command = VoiceCommand(VoiceCommandType.TIME_QUERY, "what time is it")
        detection = DetectionResult("person", 0.8)

        session.add_command(command)
        session.add_detection(detection)

        self.assertEqual(len(session.commands_processed), 1)
        self.assertEqual(len(session.detections_made), 1)
        self.assertTrue(session.is_active)

        session.end_session()
        self.assertFalse(session.is_active)
        self.assertGreater(session.total_duration, 0)

    def test_processing_stats(self):
        """Test ProcessingStats calculations."""
        stats = ProcessingStats()

        stats.update_command_stats(True, 1.5)
        stats.update_command_stats(False, 2.0)
        stats.update_command_stats(True, 1.0)

        self.assertEqual(stats.total_commands, 3)
        self.assertEqual(stats.successful_commands, 2)
        self.assertEqual(stats.failed_commands, 1)
        self.assertAlmostEqual(stats.average_processing_time, 1.5, places=2)
        self.assertAlmostEqual(stats.get_success_rate(), 66.67, places=2)


class TestUtils(unittest.TestCase):
    """Test cases for utility functions."""

    def test_parse_voice_command(self):
        """Test voice command parsing."""
        result = parse_voice_command("play music on youtube")

        self.assertEqual(result["action"], "play")
        self.assertEqual(result["target"], "youtube")
        self.assertIn("music", result["original_text"])

    def test_validate_file_path(self):
        """Test file path validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test existing file
            test_file = os.path.join(temp_dir, "test.txt")
            with open(test_file, 'w') as f:
                f.write("test")

            self.assertTrue(validate_file_path(test_file, must_exist=True))

            # Test non-existing file in existing directory
            new_file = os.path.join(temp_dir, "new.txt")
            self.assertTrue(validate_file_path(new_file, must_exist=False))

            # Test invalid path
            self.assertFalse(validate_file_path("/invalid/path/file.txt"))

    def test_format_timestamp(self):
        """Test timestamp formatting."""
        dt = datetime(2023, 12, 25, 15, 30, 45)
        formatted = format_timestamp(dt)

        self.assertEqual(formatted, "2023-12-25 15:30:45")

    def test_create_session_id(self):
        """Test session ID creation."""
        session_id = create_session_id()

        self.assertTrue(session_id.startswith("session_"))
        self.assertGreater(len(session_id), 20)  # Should be reasonably long

        # Test uniqueness
        session_id2 = create_session_id()
        self.assertNotEqual(session_id, session_id2)

    def test_config_operations(self):
        """Test configuration file operations."""
        config = {"voice_rate": 200, "camera_index": 0}

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = os.path.join(temp_dir, "config.json")

            # Test save
            save_config_to_file(config, config_file)
            self.assertTrue(os.path.exists(config_file))

            # Test load
            loaded_config = load_config_from_file(config_file)
            self.assertEqual(loaded_config["voice_rate"], 200)
            self.assertEqual(loaded_config["camera_index"], 0)


class TestSpeechProcessor(unittest.TestCase):
    """Test cases for speech processing components."""

    def setUp(self):
        """Set up test fixtures."""
        self.audio_config = AudioConfig()
        self.processor = SpeechProcessor(self.audio_config)

    def test_command_patterns_initialization(self):
        """Test that command patterns are properly initialized."""
        self.assertIn("wikipedia_search", self.processor.command_patterns)
        self.assertIn("youtube_play", self.processor.command_patterns)
        self.assertIn("time_query", self.processor.command_patterns)

    def test_synonym_mapping(self):
        """Test synonym resolution."""
        self.assertIn("google", self.processor.synonym_map)
        self.assertIn("youtube", self.processor.synonym_map)

    def test_parse_command_wikipedia(self):
        """Test parsing wikipedia search command."""
        command = self.processor.parse_command("search wikipedia for python programming")

        self.assertEqual(command.command_type, VoiceCommandType.WIKIPEDIA_SEARCH)
        self.assertEqual(command.parsed_parameters["query"], "python programming")
        self.assertGreater(command.confidence_score, 0)

    def test_parse_command_youtube(self):
        """Test parsing youtube play command."""
        command = self.processor.parse_command("play python tutorial on youtube")

        self.assertEqual(command.command_type, VoiceCommandType.YOUTUBE_PLAY)
        self.assertEqual(command.parsed_parameters["query"], "python tutorial")
        self.assertGreater(command.confidence_score, 0)

    def test_parse_command_time(self):
        """Test parsing time query command."""
        command = self.processor.parse_command("what time is it")

        self.assertEqual(command.command_type, VoiceCommandType.TIME_QUERY)
        self.assertGreater(command.confidence_score, 0)

    @patch('speech_recognition.Recognizer')
    @patch('speech_recognition.Microphone')
    def test_listen_and_recognize_success(self, mock_microphone, mock_recognizer):
        """Test successful speech recognition."""
        # Mock the speech recognition components
        mock_recognizer_instance = Mock()
        mock_recognizer.return_value = mock_recognizer_instance
        mock_recognizer_instance.recognize_google.return_value = "hello world"

        mock_microphone_instance = Mock()
        mock_microphone.return_value.__enter__ = Mock(return_value=mock_microphone_instance)
        mock_microphone.return_value.__exit__ = Mock(return_value=None)

        result = self.processor.listen_and_recognize(timeout=1)

        self.assertEqual(result, "hello world")
        self.assertEqual(self.processor.processing_stats["successful_recognitions"], 1)

    @patch('speech_recognition.Recognizer')
    @patch('speech_recognition.Microphone')
    def test_listen_and_recognize_failure(self, mock_microphone, mock_recognizer):
        """Test failed speech recognition."""
        from speech_recognition import UnknownValueError

        mock_recognizer_instance = Mock()
        mock_recognizer.return_value = mock_recognizer_instance
        mock_recognizer_instance.listen.side_effect = UnknownValueError()

        mock_microphone_instance = Mock()
        mock_microphone.return_value.__enter__ = Mock(return_value=mock_microphone_instance)
        mock_microphone.return_value.__exit__ = Mock(return_value=None)

        result = self.processor.listen_and_recognize(timeout=1)

        self.assertIsNone(result)
        self.assertEqual(self.processor.processing_stats["failed_recognitions"], 1)


class TestTextToSpeechEngine(unittest.TestCase):
    """Test cases for text-to-speech engine."""

    def setUp(self):
        """Set up test fixtures."""
        self.voice_config = {"rate": 200, "volume": 0.8, "engine": "sapi5"}
        self.tts = TextToSpeechEngine(self.voice_config)

    @patch('pyttsx3.init')
    def test_initialization_success(self, mock_init):
        """Test successful TTS initialization."""
        mock_engine = Mock()
        mock_init.return_value = mock_engine

        tts = TextToSpeechEngine(self.voice_config)

        self.assertIsNotNone(tts.engine)
        mock_engine.setProperty.assert_called()

    @patch('pyttsx3.init')
    def test_speak_success(self, mock_init):
        """Test successful text-to-speech."""
        mock_engine = Mock()
        mock_init.return_value = mock_engine

        tts = TextToSpeechEngine(self.voice_config)
        result = tts.speak("Hello world")

        self.assertTrue(result)
        mock_engine.say.assert_called_with("Hello world")
        mock_engine.runAndWait.assert_called_once()

    @patch('pyttsx3.init')
    def test_speak_failure(self, mock_init):
        """Test failed text-to-speech."""
        mock_engine = Mock()
        mock_engine.say.side_effect = Exception("TTS error")
        mock_init.return_value = mock_engine

        tts = TextToSpeechEngine(self.voice_config)
        result = tts.speak("Hello world")

        self.assertFalse(result)


class TestDataManager(unittest.TestCase):
    """Test cases for data management."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_manager = DataManager(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_session_save_and_load(self):
        """Test saving and loading sessions."""
        session = SessionData("test_session_123")

        command = VoiceCommand(VoiceCommandType.WIKIPEDIA_SEARCH, "test query")
        detection = DetectionResult("person", 0.9)

        session.add_command(command)
        session.add_detection(detection)

        # Test save
        success = self.data_manager.save_session(session)
        self.assertTrue(success)

        # Test load
        loaded_session = self.data_manager.load_session("test_session_123")
        self.assertIsNotNone(loaded_session)
        self.assertEqual(loaded_session.session_id, "test_session_123")
        self.assertEqual(len(loaded_session.commands_processed), 1)
        self.assertEqual(len(loaded_session.detections_made), 1)

    def test_config_save_and_load(self):
        """Test saving and loading configuration."""
        config = {"voice_rate": 180, "camera_index": 1}

        # Test save
        success = self.data_manager.save_config(config)
        self.assertTrue(success)

        # Test load
        loaded_config = self.data_manager.load_config()
        self.assertEqual(loaded_config["voice_rate"], 180)
        self.assertEqual(loaded_config["camera_index"], 1)

    def test_statistics_operations(self):
        """Test statistics operations."""
        stats = ProcessingStats()
        stats.update_command_stats(True, 1.2)
        stats.update_command_stats(False, 2.1)

        # Test save
        success = self.data_manager.save_statistics(stats)
        self.assertTrue(success)

        # Test load
        loaded_stats = self.data_manager.load_statistics()
        self.assertIsNotNone(loaded_stats)
        self.assertEqual(loaded_stats.total_commands, 2)
        self.assertEqual(loaded_stats.successful_commands, 1)

    def test_database_stats(self):
        """Test database statistics retrieval."""
        stats = self.data_manager.get_database_stats()

        self.assertIsInstance(stats, dict)
        self.assertIn("sessions_count", stats)
        self.assertIn("database_size_bytes", stats)


class TestErrorHandler(unittest.TestCase):
    """Test cases for error handling."""

    def setUp(self):
        """Set up test fixtures."""
        self.error_handler = ErrorHandler()

    def test_error_handling(self):
        """Test basic error handling."""
        context = ErrorContext(
            component="TestComponent",
            operation="test_operation",
            session_id="test_session"
        )

        error = ValueError("Test error")
        error_id = self.error_handler.handle_error(error, context)

        self.assertTrue(error_id.startswith("err_"))
        self.assertIn(error_id, self.error_handler.error_records)

        record = self.error_handler.error_records[error_id]
        self.assertEqual(record.message, "Test error")
        self.assertEqual(record.category, ErrorCategory.UNKNOWN)
        self.assertEqual(record.severity, ErrorSeverity.MEDIUM)

    def test_error_categorization(self):
        """Test error categorization."""
        # Test speech recognition error
        context = ErrorContext(component="SpeechProcessor", operation="listen")
        error = Exception("Speech recognition failed")

        error_id = self.error_handler.handle_error(error, context)
        record = self.error_handler.error_records[error_id]

        self.assertEqual(record.category, ErrorCategory.SPEECH_RECOGNITION)

    def test_error_summary(self):
        """Test error summary generation."""
        # Add a few errors
        context = ErrorContext(component="Test", operation="test")

        self.error_handler.handle_error(ValueError("Error 1"), context)
        self.error_handler.handle_error(RuntimeError("Error 2"), context)

        summary = self.error_handler.get_error_summary()

        self.assertEqual(summary["total_errors"], 2)
        self.assertIn("error_counts_by_category", summary)
        self.assertIn("recent_errors", summary)

    def test_error_cleanup(self):
        """Test error cleanup functionality."""
        context = ErrorContext(component="Test", operation="test")

        # Add an error and mark it resolved
        error_id = self.error_handler.handle_error(ValueError("Test error"), context)
        self.error_handler.error_records[error_id].mark_resolved()

        # Set the timestamp to be old
        old_time = datetime.now() - timedelta(days=10)
        self.error_handler.error_records[error_id].context.timestamp = old_time

        # Clean up old resolved errors
        cleared_count = self.error_handler.clear_resolved_errors(max_age_days=7)

        self.assertEqual(cleared_count, 1)
        self.assertNotIn(error_id, self.error_handler.error_records)


class TestSystemMonitor(unittest.TestCase):
    """Test cases for system monitoring."""

    def setUp(self):
        """Set up test fixtures."""
        self.error_handler = ErrorHandler()
        self.monitor = SystemMonitor(self.error_handler)

    @patch('speech_recognition.Microphone')
    def test_microphone_check_success(self, mock_microphone):
        """Test successful microphone check."""
        mock_microphone.return_value.__enter__ = Mock(return_value=Mock())
        mock_microphone.return_value.__exit__ = Mock(return_value=None)

        result = self.monitor._check_microphone()
        self.assertTrue(result)

    @patch('cv2.VideoCapture')
    def test_camera_check_success(self, mock_videocapture):
        """Test successful camera check."""
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_videocapture.return_value = mock_cap

        result = self.monitor._check_camera()
        self.assertTrue(result)
        mock_cap.release.assert_called_once()

    @patch('pyttsx3.init')
    def test_voice_engine_check_success(self, mock_init):
        """Test successful voice engine check."""
        mock_engine = Mock()
        mock_init.return_value = mock_engine

        result = self.monitor._check_voice_engine()
        self.assertTrue(result)

    def test_health_check(self):
        """Test comprehensive health check."""
        with patch.object(self.monitor, '_check_microphone', return_value=True), \
             patch.object(self.monitor, '_check_camera', return_value=True), \
             patch.object(self.monitor, '_check_voice_engine', return_value=True), \
             patch('utils.get_system_info', return_value={
                 "memory_percent": 50.0,
                 "memory_total": 8 * 1024 * 1024 * 1024,  # 8GB
                 "cpu_percent": 25.0
             }):

            status = self.monitor.perform_health_check()

            self.assertTrue(status.is_microphone_active)
            self.assertTrue(status.is_camera_active)
            self.assertTrue(status.is_voice_engine_active)
            self.assertEqual(status.cpu_usage_percent, 25.0)
            self.assertIsInstance(status.last_health_check, datetime)


if __name__ == '__main__':
    # Set up logging for tests
    setup_logging("WARNING")

    # Run tests
    unittest.main(verbosity=2)
