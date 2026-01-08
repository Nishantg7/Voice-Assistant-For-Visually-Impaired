# Voice Assistant Project

A comprehensive AI-powered voice assistant built with Python featuring object detection, currency recognition, weather information, calculator, notes management, and more.

## Features

- **Voice Commands**: Speech recognition and text-to-speech
- **Object Detection**: Real-time object detection using YOLO
- **Currency Recognition**: Indian rupee note detection
- **Weather Information**: Get weather updates for any city
- **Calculator**: Mathematical calculations
- **Notes Management**: Save, read, search, and manage notes
- **Web Integration**: Open websites, search YouTube, etc.
- **Jokes**: Random joke generator

## Prerequisites

- Python 3.11+
- Webcam (for vision features)
- Microphone (for voice commands)
- Internet connection (for some features)

## Setup Instructions

### 1. Clone or Download the Project

### 2. Activate Virtual Environment

**Windows (Command Prompt):**
```bash
activate_venv.bat
```

**Windows (PowerShell):**
```powershell
.\activate_venv.ps1
```

**Manual Activation:**
```bash
voice_assistant_env\Scripts\activate
```

### 3. Install Dependencies (if needed)

If packages aren't installed, run:
```bash
pip install -r requirements.txt
```

### 4. Run the Voice Assistant

```bash
python voice_assistant.py
```

## Voice Commands

The assistant responds to these commands:

- **"open camera"** - Launch object detection
- **"scan money"** - Launch currency recognition
- **"weather in [city]"** - Get weather information
- **"calculate [expression]"** - Perform calculations
- **"note [text]"** - Save a note
- **"show notes"** - Display all notes
- **"wikipedia [topic]"** - Search Wikipedia
- **"play [song]"** - Play on YouTube
- **"open [website]"** - Open websites
- **"joke"** - Tell a joke
- **"the time"** - Current time
- **"exit code"** - Close assistant

## Project Structure

```
├── voice_assistant.py      # Main application
├── object_detection.py     # Object detection module
├── money_detection.py      # Currency recognition module
├── calculator.py          # Calculator functions
├── weather.py            # Weather API integration
├── reminder.py           # Notes management
├── news.py               # News functionality
├── requirements.txt      # Python dependencies
├── activate_venv.bat     # Windows activation script
├── activate_venv.ps1     # PowerShell activation script
├── voice_assistant_env/  # Virtual environment
├── object_detection.pt   # YOLO model for objects
└── rupee.pt             # YOLO model for currency
```

## Model Files

- `object_detection.pt`: Pre-trained YOLO model for detecting common objects (books, phones, chairs, etc.)
- `rupee.pt`: Pre-trained YOLO model for detecting Indian currency denominations

## Troubleshooting

### Camera Issues
- Ensure your webcam is connected and not used by other applications
- Check camera permissions in your system settings

### Voice Recognition Issues
- Ensure your microphone is connected and set as default
- Check microphone permissions
- Speak clearly and reduce background noise

### Package Import Errors
- Make sure you're running from the activated virtual environment
- Try reinstalling requirements: `pip install -r requirements.txt`

### Permission Errors
- Run Command Prompt/PowerShell as Administrator if needed
- Ensure the virtual environment has proper permissions

## Dependencies

All required packages are listed in `requirements.txt` with tested working versions to avoid compatibility issues.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is for educational purposes. Please ensure compliance with all applicable laws and regulations when using AI and computer vision features.
