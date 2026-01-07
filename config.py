"""
Configuration management for the Voice Assistant application.
Handles loading, validation, and management of application settings.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import asdict
from models import AppConfig, AudioConfig
from utils import validate_file_path, load_config_from_file, save_config_to_file


class ConfigManager:
    """
    Manages application configuration with support for multiple sources:
    - Default values
    - Configuration files
    - Environment variables
    - Runtime overrides
    """

    def __init__(self, config_dir: str = "config"):
        """
        Initialize configuration manager.

        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)

        self.logger = logging.getLogger("voice_assistant.config_manager")

        # Configuration file paths
        self.app_config_file = self.config_dir / "app_config.json"
        self.audio_config_file = self.config_dir / "audio_config.json"
        self.user_prefs_file = self.config_dir / "user_preferences.json"

        # Runtime configuration storage
        self._app_config: Optional[AppConfig] = None
        self._audio_config: Optional[AudioConfig] = None
        self._user_preferences: Dict[str, Any] = {}

        # Configuration validation rules
        self._validation_rules = self._initialize_validation_rules()

        self.logger.info("Configuration manager initialized")

    def _initialize_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize configuration validation rules.

        Returns:
            Dictionary of validation rules for each configuration section
        """
        return {
            "app_config": {
                "voice_rate": {"type": int, "min": 50, "max": 400},
                "voice_volume": {"type": float, "min": 0.0, "max": 1.0},
                "camera_index": {"type": int, "min": 0, "max": 10},
                "detection_threshold": {"type": float, "min": 0.0, "max": 1.0},
                "max_session_duration": {"type": int, "min": 60, "max": 36000},
                "enable_logging": {"type": bool},
                "log_level": {"type": str, "allowed_values": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]}
            },
            "audio_config": {
                "sample_rate": {"type": int, "min": 8000, "max": 48000},
                "channels": {"type": int, "allowed_values": [1, 2]},
                "chunk_size": {"type": int, "min": 256, "max": 4096},
                "pause_threshold": {"type": float, "min": 0.1, "max": 2.0},
                "energy_threshold": {"type": int, "min": 0, "max": 4000},
                "dynamic_energy_threshold": {"type": bool}
            }
        }

    def load_app_config(self) -> AppConfig:
        """
        Load application configuration.

        Returns:
            AppConfig instance with loaded settings
        """
        if self._app_config is not None:
            return self._app_config

        # Start with defaults
        config = self._get_default_app_config()

        # Load from file if exists
        if self.app_config_file.exists():
            try:
                file_config = load_config_from_file(str(self.app_config_file))
                config.update(file_config)
                self.logger.info("Loaded app configuration from file")
            except Exception as e:
                self.logger.warning(f"Failed to load app config file: {e}")

        # Override with environment variables
        config = self._apply_environment_overrides(config, "VOICE_ASSISTANT_")

        # Validate configuration
        config = self._validate_config(config, "app_config")

        # Create AppConfig instance
        self._app_config = AppConfig(**config)
        return self._app_config

    def load_audio_config(self) -> AudioConfig:
        """
        Load audio configuration.

        Returns:
            AudioConfig instance with loaded settings
        """
        if self._audio_config is not None:
            return self._audio_config

        # Start with defaults
        config = self._get_default_audio_config()

        # Load from file if exists
        if self.audio_config_file.exists():
            try:
                file_config = load_config_from_file(str(self.audio_config_file))
                config.update(file_config)
                self.logger.info("Loaded audio configuration from file")
            except Exception as e:
                self.logger.warning(f"Failed to load audio config file: {e}")

        # Override with environment variables
        config = self._apply_environment_overrides(config, "AUDIO_")

        # Validate configuration
        config = self._validate_config(config, "audio_config")

        # Create AudioConfig instance
        self._audio_config = AudioConfig(**config)
        return self._audio_config

    def load_user_preferences(self) -> Dict[str, Any]:
        """
        Load user preferences.

        Returns:
            Dictionary of user preferences
        """
        if self._user_preferences:
            return self._user_preferences.copy()

        # Start with defaults
        preferences = self._get_default_user_preferences()

        # Load from file if exists
        if self.user_prefs_file.exists():
            try:
                file_prefs = load_config_from_file(str(self.user_prefs_file))
                preferences.update(file_prefs)
                self.logger.info("Loaded user preferences from file")
            except Exception as e:
                self.logger.warning(f"Failed to load user preferences file: {e}")

        self._user_preferences = preferences
        return preferences.copy()

    def save_app_config(self, config: AppConfig) -> bool:
        """
        Save application configuration to file.

        Args:
            config: AppConfig instance to save

        Returns:
            True if save was successful, False otherwise
        """
        try:
            config_dict = asdict(config)
            success = save_config_to_file(config_dict, str(self.app_config_file))

            if success:
                self._app_config = config
                self.logger.info("App configuration saved successfully")

            return success

        except Exception as e:
            self.logger.error(f"Failed to save app configuration: {e}")
            return False

    def save_audio_config(self, config: AudioConfig) -> bool:
        """
        Save audio configuration to file.

        Args:
            config: AudioConfig instance to save

        Returns:
            True if save was successful, False otherwise
        """
        try:
            config_dict = asdict(config)
            success = save_config_to_file(config_dict, str(self.audio_config_file))

            if success:
                self._audio_config = config
                self.logger.info("Audio configuration saved successfully")

            return success

        except Exception as e:
            self.logger.error(f"Failed to save audio configuration: {e}")
            return False

    def save_user_preferences(self, preferences: Dict[str, Any]) -> bool:
        """
        Save user preferences to file.

        Args:
            preferences: User preferences dictionary

        Returns:
            True if save was successful, False otherwise
        """
        try:
            success = save_config_to_file(preferences, str(self.user_prefs_file))

            if success:
                self._user_preferences = preferences.copy()
                self.logger.info("User preferences saved successfully")

            return success

        except Exception as e:
            self.logger.error(f"Failed to save user preferences: {e}")
            return False

    def _get_default_app_config(self) -> Dict[str, Any]:
        """Get default application configuration."""
        return {
            "voice_engine": "sapi5",
            "voice_rate": 200,
            "voice_volume": 0.8,
            "recognition_language": "en-in",
            "camera_index": 0,
            "detection_threshold": 0.5,
            "max_session_duration": 3600,
            "enable_logging": True,
            "log_level": "INFO",
            "object_detection_model": "object_detection.pt",
            "money_detection_model": "rupee.pt",
            "object_classes": [
                'book', 'car', 'cell phone', 'chair', 'cup', 'glasses',
                'laptop', 'pen', 'person', 'plant', 'screen'
            ],
            "money_classes": [
                '10', '100', '20', '200', '2000', '50', '500'
            ]
        }

    def _get_default_audio_config(self) -> Dict[str, Any]:
        """Get default audio configuration."""
        return {
            "sample_rate": 44100,
            "channels": 1,
            "chunk_size": 1024,
            "pause_threshold": 0.5,
            "energy_threshold": 300,
            "dynamic_energy_threshold": True
        }

    def _get_default_user_preferences(self) -> Dict[str, Any]:
        """Get default user preferences."""
        return {
            "theme": "dark",
            "language": "en",
            "enable_voice_feedback": True,
            "auto_start_camera": False,
            "notification_sound": True,
            "save_session_history": True,
            "max_history_days": 30,
            "favorite_commands": [],
            "custom_commands": {}
        }

    def _apply_environment_overrides(self, config: Dict[str, Any], prefix: str) -> Dict[str, Any]:
        """
        Apply environment variable overrides to configuration.

        Args:
            config: Base configuration dictionary
            prefix: Environment variable prefix

        Returns:
            Updated configuration dictionary
        """
        updated_config = config.copy()

        for key in config.keys():
            env_key = f"{prefix}{key.upper()}"
            env_value = os.environ.get(env_key)

            if env_value is not None:
                # Type conversion based on original value type
                original_value = config[key]
                if isinstance(original_value, bool):
                    updated_config[key] = env_value.lower() in ('true', '1', 'yes', 'on')
                elif isinstance(original_value, int):
                    try:
                        updated_config[key] = int(env_value)
                    except ValueError:
                        self.logger.warning(f"Invalid integer value for {env_key}: {env_value}")
                elif isinstance(original_value, float):
                    try:
                        updated_config[key] = float(env_value)
                    except ValueError:
                        self.logger.warning(f"Invalid float value for {env_key}: {env_value}")
                elif isinstance(original_value, list):
                    # For lists, assume comma-separated values
                    updated_config[key] = [item.strip() for item in env_value.split(',')]
                else:
                    updated_config[key] = env_value

                self.logger.debug(f"Applied environment override: {key} = {updated_config[key]}")

        return updated_config

    def _validate_config(self, config: Dict[str, Any], config_type: str) -> Dict[str, Any]:
        """
        Validate configuration against validation rules.

        Args:
            config: Configuration to validate
            config_type: Type of configuration (for validation rules)

        Returns:
            Validated configuration (with invalid values corrected)
        """
        if config_type not in self._validation_rules:
            return config

        rules = self._validation_rules[config_type]
        validated_config = config.copy()

        for key, value in config.items():
            if key not in rules:
                continue

            rule = rules[key]
            expected_type = rule.get("type")

            # Type validation
            if expected_type and not isinstance(value, expected_type):
                try:
                    if expected_type == bool:
                        validated_config[key] = str(value).lower() in ('true', '1', 'yes', 'on')
                    else:
                        validated_config[key] = expected_type(value)
                except (ValueError, TypeError):
                    self.logger.warning(f"Invalid type for {key}, using default")
                    # Keep original value if conversion fails

            # Range validation
            if "min" in rule and isinstance(value, (int, float)):
                if value < rule["min"]:
                    self.logger.warning(f"Value for {key} below minimum, using {rule['min']}")
                    validated_config[key] = rule["min"]

            if "max" in rule and isinstance(value, (int, float)):
                if value > rule["max"]:
                    self.logger.warning(f"Value for {key} above maximum, using {rule['max']}")
                    validated_config[key] = rule["max"]

            # Allowed values validation
            if "allowed_values" in rule:
                if value not in rule["allowed_values"]:
                    default_value = rule.get("default", rule["allowed_values"][0])
                    self.logger.warning(f"Invalid value for {key}, using {default_value}")
                    validated_config[key] = default_value

        return validated_config

    def get_config_summary(self) -> Dict[str, Any]:
        """
        Get a summary of current configuration.

        Returns:
            Configuration summary dictionary
        """
        return {
            "app_config_loaded": self._app_config is not None,
            "audio_config_loaded": self._audio_config is not None,
            "user_prefs_loaded": bool(self._user_preferences),
            "config_files": {
                "app_config": str(self.app_config_file),
                "audio_config": str(self.audio_config_file),
                "user_preferences": str(self.user_prefs_file)
            },
            "config_files_exist": {
                "app_config": self.app_config_file.exists(),
                "audio_config": self.audio_config_file.exists(),
                "user_preferences": self.user_prefs_file.exists()
            }
        }

    def reset_to_defaults(self) -> None:
        """
        Reset all configurations to default values.
        """
        self._app_config = None
        self._audio_config = None
        self._user_preferences.clear()

        # Remove config files
        for config_file in [self.app_config_file, self.audio_config_file, self.user_prefs_file]:
            if config_file.exists():
                try:
                    config_file.unlink()
                    self.logger.info(f"Removed config file: {config_file}")
                except Exception as e:
                    self.logger.warning(f"Failed to remove config file {config_file}: {e}")

        self.logger.info("Configuration reset to defaults")

    def create_example_configs(self) -> None:
        """
        Create example configuration files for reference.
        """
        example_app_config = {
            "_comment": "Example application configuration",
            "voice_engine": "sapi5",
            "voice_rate": 180,
            "voice_volume": 0.9,
            "recognition_language": "en-in",
            "camera_index": 0,
            "detection_threshold": 0.6,
            "max_session_duration": 7200,
            "enable_logging": True,
            "log_level": "DEBUG"
        }

        example_audio_config = {
            "_comment": "Example audio configuration",
            "sample_rate": 48000,
            "channels": 1,
            "chunk_size": 2048,
            "pause_threshold": 0.8,
            "energy_threshold": 400,
            "dynamic_energy_threshold": True
        }

        example_user_prefs = {
            "_comment": "Example user preferences",
            "theme": "light",
            "language": "en",
            "enable_voice_feedback": True,
            "auto_start_camera": True,
            "notification_sound": False,
            "save_session_history": True,
            "max_history_days": 60,
            "favorite_commands": ["time", "wikipedia", "camera"],
            "custom_commands": {
                "my_music": "play favorite music on youtube",
                "check_weather": "search weather in browser"
            }
        }

        try:
            save_config_to_file(example_app_config, str(self.config_dir / "app_config.example.json"))
            save_config_to_file(example_audio_config, str(self.config_dir / "audio_config.example.json"))
            save_config_to_file(example_user_prefs, str(self.config_dir / "user_preferences.example.json"))

            self.logger.info("Created example configuration files")

        except Exception as e:
            self.logger.error(f"Failed to create example configs: {e}")


def create_default_config_files():
    """
    Create default configuration files if they don't exist.
    This is a utility function for initial setup.
    """
    config_manager = ConfigManager()

    # Create example files
    config_manager.create_example_configs()

    # Create basic config files with defaults
    if not config_manager.app_config_file.exists():
        app_config = config_manager.load_app_config()
        config_manager.save_app_config(app_config)

    if not config_manager.audio_config_file.exists():
        audio_config = config_manager.load_audio_config()
        config_manager.save_audio_config(audio_config)

    if not config_manager.user_prefs_file.exists():
        user_prefs = config_manager.load_user_preferences()
        config_manager.save_user_preferences(user_prefs)


if __name__ == "__main__":
    # Example usage
    config_manager = ConfigManager()

    # Load configurations
    app_config = config_manager.load_app_config()
    audio_config = config_manager.load_audio_config()
    user_prefs = config_manager.load_user_preferences()

    print("App Config Voice Rate:", app_config.voice_rate)
    print("Audio Config Sample Rate:", audio_config.sample_rate)
    print("User Theme:", user_prefs.get("theme"))

    # Create example files
    config_manager.create_example_configs()
    print("Example configuration files created")
