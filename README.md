# Enhanced Voice Assistant with Computer Vision

A comprehensive voice-controlled assistant application that integrates speech recognition, computer vision, data persistence, and advanced error handling. This enhanced version demonstrates complex software architecture with multiple interconnected modules.

## Features

### Core Voice Assistant Features
- **Speech Recognition**: Advanced speech-to-text using Google Speech Recognition API
- **Text-to-Speech**: Natural voice synthesis with customizable voice settings
- **Command Processing**: Intelligent command parsing and execution
- **Wikipedia Integration**: Search and retrieve information from Wikipedia
- **YouTube Integration**: Search and play videos on YouTube
- **Web Browser Control**: Open websites and perform web searches
- **Time Queries**: Get current time information
- **Entertainment**: Tell jokes and provide entertainment

### Computer Vision Features
- **Object Detection**: Real-time object detection using YOLOv8
- **Money Detection**: Specialized currency/note recognition
- **Live Camera Feed**: Real-time video processing with GUI
- **Multi-threading**: Concurrent camera operations

### Advanced System Features
- **Session Management**: Track user interactions and sessions
- **Data Persistence**: SQLite database for storing sessions and statistics
- **Configuration Management**: Flexible configuration system with environment variable support
- **Error Handling**: Comprehensive error handling with recovery strategies
- **System Monitoring**: Health checks and system status monitoring
- **Logging**: Structured logging with multiple log levels
- **Statistics Tracking**: Performance metrics and usage statistics

## Project Structure

```
test-repo/
├── enhanced_voice_assistant.py    # Main application with full integration
├── voice_assistant.py             # Original simplified version
├── object_detection.py            # Object detection with camera GUI
├── money_detection.py             # Money/currency detection
├── models.py                      # Data models and configurations
├── utils.py                       # Utility functions and helpers
├── speech_processor.py            # Advanced speech processing
├── data_manager.py                # Data persistence and management
├── error_handler.py               # Error handling and monitoring
├── config.py                      # Configuration management
├── test_voice_assistant.py        # Comprehensive unit tests
├── requirements.txt               # Python dependencies
├── config/                        # Configuration files directory
│   ├── app_config.example.json
│   ├── audio_config.example.json
│   └── user_preferences.example.json
├── data/                          # Data storage directory (created at runtime)
├── logs/                          # Log files directory (created at runtime)
└── README.md                      # This documentation
```

## Architecture Overview

### Core Components

1. **EnhancedVoiceAssistant** (`enhanced_voice_assistant.py`)
   - Main application class integrating all components
   - GUI management using Tkinter
   - Session lifecycle management
   - Command routing and execution

2. **Speech Processing** (`speech_processor.py`)
   - Speech recognition with noise calibration
   - Command parsing and classification
   - Text-to-speech synthesis

3. **Data Management** (`data_manager.py`)
   - SQLite database operations
   - Session data persistence
   - Statistics tracking
   - CSV export functionality

4. **Error Handling** (`error_handler.py`)
   - Comprehensive error categorization
   - Recovery strategies for different error types
   - System monitoring and health checks

5. **Configuration** (`config.py`)
   - Multi-source configuration loading
   - Environment variable support
   - Validation and type checking

### Data Models

- **VoiceCommand**: Represents parsed voice commands with metadata
- **DetectionResult**: Object/money detection results with confidence scores
- **SessionData**: User session tracking with commands and detections
- **AppConfig**: Application configuration settings
- **ProcessingStats**: Performance and usage statistics

## Installation and Setup

### Prerequisites
- Python 3.8 or higher
- Webcam for computer vision features
- Microphone for speech recognition
- Internet connection for online services

### Installation Steps

1. **Clone or set up the repository**:
   ```bash
   cd test-repo
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the application** (optional):
   - Copy example configuration files:
     ```bash
     cp config/app_config.example.json config/app_config.json
     cp config/audio_config.example.json config/audio_config.json
     cp config/user_preferences.example.json config/user_preferences.json
     ```
   - Edit configuration files as needed

4. **Download YOLO models**:
   - Ensure `object_detection.pt` and `rupee.pt` are in the same directory
   - These are pre-trained YOLOv8 models for object and currency detection

### Running the Application

#### Enhanced Version (Recommended)
```bash
python enhanced_voice_assistant.py
```

#### Original Version
```bash
python voice_assistant.py
```

#### Individual Components
```bash
# Object detection only
python object_detection.py

# Money detection only
python money_detection.py
```

## Usage

### Voice Commands

The assistant supports various voice commands:

- **"Search Wikipedia for [topic]"** - Search and read Wikipedia articles
- **"Play [song/video] on YouTube"** - Play content on YouTube
- **"Open [website]"** - Open websites (Google, Stack Overflow, Netflix, etc.)
- **"What time is it?"** - Get current time
- **"Tell me a joke"** - Get a random joke
- **"Open camera"** - Start object detection
- **"Scan money"** - Start currency detection
- **"Exit" or "Stop"** - Stop the assistant

### GUI Interface

The main application provides a graphical interface with:
- **Start/Stop buttons** for voice listening
- **Status display** showing current operation
- **Statistics display** showing command counts
- **Health check button** for system diagnostics

## Configuration

### Application Configuration (`config/app_config.json`)
```json
{
  "voice_engine": "sapi5",
  "voice_rate": 200,
  "voice_volume": 0.8,
  "camera_index": 0,
  "detection_threshold": 0.5,
  "enable_logging": true,
  "log_level": "INFO"
}
```

### Audio Configuration (`config/audio_config.json`)
```json
{
  "sample_rate": 44100,
  "channels": 1,
  "pause_threshold": 0.5,
  "energy_threshold": 300,
  "dynamic_energy_threshold": true
}
```

### User Preferences (`config/user_preferences.json`)
```json
{
  "theme": "dark",
  "language": "en",
  "enable_voice_feedback": true,
  "auto_start_camera": false,
  "save_session_history": true
}
```

## Testing

Run the comprehensive test suite:
```bash
python -m pytest test_voice_assistant.py -v
```

Or run specific test categories:
```bash
python test_voice_assistant.py
```

## Data Storage

The application creates several data directories:

- **`data/`**: SQLite database and session data
- **`logs/`**: Application log files
- **`config/`**: Configuration files (if created)

### Database Schema

The application uses SQLite with the following main tables:
- **sessions**: User session information
- **commands**: Voice commands processed
- **detections**: Object/money detection results
- **daily_stats**: Daily usage statistics

## Error Handling and Recovery

The system includes comprehensive error handling:

- **Speech Recognition Errors**: Automatic microphone recalibration
- **Network Errors**: Graceful degradation with retry logic
- **File System Errors**: Directory creation and permission handling
- **Hardware Errors**: Detection and user notification
- **Critical Errors**: System shutdown with data preservation

## Performance Optimization

- **Multi-threading**: Concurrent camera operations and GUI updates
- **Semaphore-based rate limiting**: Prevents API quota exhaustion
- **Lazy loading**: Components initialized on demand
- **Memory management**: Automatic cleanup of temporary resources

## Security Considerations

- **Input validation**: All voice inputs are validated and sanitized
- **Error logging**: Sensitive information is not logged
- **File permissions**: Secure file access patterns
- **Network security**: Safe handling of web requests

## Troubleshooting

### Common Issues

1. **Microphone not working**:
   - Check microphone permissions
   - Run microphone calibration
   - Verify audio drivers

2. **Camera not accessible**:
   - Check camera permissions
   - Ensure no other applications are using the camera
   - Try different camera indices in configuration

3. **Speech recognition errors**:
   - Check internet connection
   - Reduce background noise
   - Adjust microphone sensitivity

4. **Model loading errors**:
   - Verify YOLO model files exist
   - Check file permissions
   - Ensure compatible PyTorch version

### Debug Mode

Enable debug logging by setting log level to "DEBUG" in configuration:
```json
{
  "log_level": "DEBUG"
}
```

## Development

### Adding New Features

1. **Create new command types** in `models.py`
2. **Implement command logic** in `EnhancedVoiceAssistant.execute_command()`
3. **Add command patterns** in `speech_processor.py`
4. **Update tests** in `test_voice_assistant.py`

### Extending Computer Vision

1. **Add new detection classes** in model configurations
2. **Create new detection modules** following the existing pattern
3. **Integrate with main assistant** in command execution

### Database Extensions

1. **Add new tables** in `data_manager.py`
2. **Create migration scripts** for schema updates
3. **Update data models** in `models.py`

## License

This project is developed for educational and testing purposes.

## Contributing

This repository is designed to test documentation generation systems. To contribute:

1. Add more complex functions and classes
2. Increase inter-module dependencies
3. Add comprehensive error handling
4. Include detailed docstrings
5. Create additional test cases

## Documentation Generation Testing

This repository is specifically structured to test documentation generation systems by including:

- **Complex class hierarchies** with inheritance and composition
- **Interconnected modules** with cross-references
- **Advanced error handling** and logging
- **Configuration management** with multiple sources
- **Data persistence** with database operations
- **Multi-threading** and concurrency
- **Comprehensive test suites**
- **Type hints** and documentation strings
- **Multiple architectural patterns** (MVC, Repository, Factory, etc.)

The goal is to create a codebase that thoroughly exercises documentation generation algorithms and tests their ability to understand complex software architectures.
