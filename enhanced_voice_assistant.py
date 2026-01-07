"""
Enhanced Voice Assistant - Integrated implementation using all modules.
This is the main application that brings together all components for a complete voice assistant system.
"""

import tkinter as tk
import threading
import datetime
import wikipedia
import webbrowser
import os
import pywhatkit
import pyjokes
import subprocess
import time
import logging
from typing import Optional, Dict, Any
from pathlib import Path

# Import our custom modules
from models import (
    VoiceCommand, VoiceCommandType, DetectionResult, SessionData,
    AppConfig, AudioConfig, ProcessingStats, SystemStatus
)
from utils import setup_logging, create_session_id, format_timestamp, timing_decorator
from speech_processor import SpeechProcessor, TextToSpeechEngine
from data_manager import DataManager
from error_handler import ErrorHandler, ErrorSeverity, ErrorCategory, ErrorContext, SystemMonitor
from config import ConfigManager


class EnhancedVoiceAssistant:
    """
    Enhanced voice assistant that integrates all system components.
    Provides a complete voice-controlled interface with advanced features.
    """

    def __init__(self):
        """
        Initialize the enhanced voice assistant with all components.
        """
        # Initialize configuration
        self.config_manager = ConfigManager()
        self.app_config = self.config_manager.load_app_config()
        self.audio_config = self.config_manager.load_audio_config()
        self.user_preferences = self.config_manager.load_user_preferences()

        # Initialize logging
        self.logger = setup_logging(
            log_level=self.app_config.log_level,
            log_file="logs/voice_assistant.log" if self.app_config.enable_logging else None
        )

        # Initialize core components
        self.error_handler = ErrorHandler(log_level=self.app_config.log_level)
        self.system_monitor = SystemMonitor(self.error_handler)
        self.data_manager = DataManager(data_dir="data")

        # Initialize speech components
        self.speech_processor = SpeechProcessor(self.audio_config)
        self.tts_engine = TextToSpeechEngine({
            "engine": self.app_config.voice_engine,
            "rate": self.app_config.voice_rate,
            "volume": self.app_config.voice_volume
        })

        # Session management
        self.current_session: Optional[SessionData] = None
        self.listening_enabled = False

        # Statistics tracking
        self.stats = ProcessingStats()

        # UI components (will be initialized when GUI is created)
        self.root: Optional[tk.Tk] = None
        self.listen_button: Optional[tk.Button] = None
        self.stop_button: Optional[tk.Button] = None
        self.status_label: Optional[tk.Label] = None
        self.stats_label: Optional[tk.Label] = None

        self.logger.info("Enhanced Voice Assistant initialized successfully")

    def create_session(self) -> SessionData:
        """
        Create a new session for tracking user interactions.

        Returns:
            New SessionData instance
        """
        session_id = create_session_id()
        session = SessionData(session_id)

        self.current_session = session
        self.logger.info(f"Created new session: {session_id}")

        return session

    def end_session(self) -> None:
        """End the current session and save data."""
        if self.current_session and self.current_session.is_active:
            self.current_session.end_session()

            # Save session data
            success = self.data_manager.save_session(self.current_session)
            if success:
                self.logger.info(f"Session {self.current_session.session_id} saved successfully")
            else:
                self.logger.error(f"Failed to save session {self.current_session.session_id}")

            # Update statistics
            self.data_manager.save_statistics(self.stats)

        self.current_session = None

    @timing_decorator
    def process_voice_command(self, raw_text: str) -> bool:
        """
        Process a voice command using the enhanced speech processor.

        Args:
            raw_text: Raw recognized text

        Returns:
            True if command was processed successfully, False otherwise
        """
        start_time = time.time()

        try:
            # Parse command using speech processor
            command = self.speech_processor.parse_command(raw_text)

            # Add to session if active
            if self.current_session:
                self.current_session.add_command(command)

            # Execute command
            success = self.execute_command(command)

            # Update statistics
            processing_time = time.time() - start_time
            self.stats.update_command_stats(success, processing_time)

            return success

        except Exception as e:
            # Handle errors
            context = ErrorContext(
                component="EnhancedVoiceAssistant",
                operation="process_voice_command",
                session_id=self.current_session.session_id if self.current_session else None,
                parameters={"raw_text": raw_text}
            )

            self.error_handler.handle_error(e, context, ErrorSeverity.MEDIUM)
            return False

    def execute_command(self, command: VoiceCommand) -> bool:
        """
        Execute a parsed voice command.

        Args:
            command: Parsed VoiceCommand object

        Returns:
            True if execution was successful, False otherwise
        """
        try:
            if command.command_type == VoiceCommandType.WIKIPEDIA_SEARCH:
                return self._execute_wikipedia_search(command)
            elif command.command_type == VoiceCommandType.YOUTUBE_SEARCH:
                return self._execute_youtube_search(command)
            elif command.command_type == VoiceCommandType.YOUTUBE_PLAY:
                return self._execute_youtube_play(command)
            elif command.command_type == VoiceCommandType.WEB_BROWSER:
                return self._execute_web_browser(command)
            elif command.command_type == VoiceCommandType.TIME_QUERY:
                return self._execute_time_query()
            elif command.command_type == VoiceCommandType.JOKE:
                return self._execute_joke()
            elif command.command_type == VoiceCommandType.CAMERA_CONTROL:
                return self._execute_camera_control()
            elif command.command_type == VoiceCommandType.MONEY_DETECTION:
                return self._execute_money_detection()
            elif command.command_type == VoiceCommandType.OBJECT_DETECTION:
                return self._execute_object_detection()
            elif command.command_type == VoiceCommandType.SYSTEM_CONTROL:
                return self._execute_system_control()
            else:
                self.speak("I'm sorry, I didn't understand that command.")
                return False

        except Exception as e:
            context = ErrorContext(
                component="EnhancedVoiceAssistant",
                operation="execute_command",
                session_id=self.current_session.session_id if self.current_session else None,
                parameters={"command_type": command.command_type.value}
            )
            self.error_handler.handle_error(e, context, ErrorSeverity.MEDIUM)
            return False

    def _execute_wikipedia_search(self, command: VoiceCommand) -> bool:
        """Execute Wikipedia search command."""
        query = command.parsed_parameters.get("query", "").strip()
        if not query:
            self.speak("What would you like me to search on Wikipedia?")
            return False

        self.speak(f'Searching Wikipedia for {query}...')
        try:
            results = wikipedia.summary(query, sentences=2)
            self.speak("According to Wikipedia")
            self.speak(results)
            return True
        except wikipedia.exceptions.DisambiguationError:
            self.speak("I found multiple results. Please be more specific.")
            return False
        except wikipedia.exceptions.PageError:
            self.speak("I couldn't find any information on that topic.")
            return False

    def _execute_youtube_search(self, command: VoiceCommand) -> bool:
        """Execute YouTube search command."""
        query = command.parsed_parameters.get("query", "").strip()
        if not query:
            self.speak("What would you like me to search on YouTube?")
            return False

        self.speak(f'Searching YouTube for {query}')
        try:
            webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
            return True
        except Exception as e:
            self.logger.error(f"YouTube search failed: {e}")
            return False

    def _execute_youtube_play(self, command: VoiceCommand) -> bool:
        """Execute YouTube play command."""
        query = command.parsed_parameters.get("query", "").strip()
        if not query:
            self.speak("What would you like me to play?")
            return False

        self.speak(f'Playing {query}')
        try:
            pywhatkit.playonyt(query)
            return True
        except Exception as e:
            self.logger.error(f"YouTube play failed: {e}")
            return False

    def _execute_web_browser(self, command: VoiceCommand) -> bool:
        """Execute web browser command."""
        target = command.parsed_parameters.get("target", "").lower().strip()

        if not target:
            self.speak("Which website would you like me to open?")
            return False

        # Handle common websites
        website_map = {
            "google": "https://www.google.com",
            "stackoverflow": "https://www.stackoverflow.com",
            "netflix": "https://www.netflix.com",
            "youtube": "https://www.youtube.com"
        }

        if target in website_map:
            url = website_map[target]
        else:
            # Assume it's a direct URL or search term
            if "." in target:
                url = f"https://{target}"
            else:
                url = f"https://www.google.com/search?q={target}"

        try:
            webbrowser.open(url)
            self.speak(f"Opening {target}")
            return True
        except Exception as e:
            self.logger.error(f"Web browser command failed: {e}")
            return False

    def _execute_time_query(self) -> bool:
        """Execute time query command."""
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        self.speak(f"The current time is {current_time}")
        return True

    def _execute_joke(self) -> bool:
        """Execute joke command."""
        try:
            joke = pyjokes.get_joke()
            self.speak(joke)
            return True
        except Exception as e:
            self.logger.error(f"Joke retrieval failed: {e}")
            return False

    def _execute_camera_control(self) -> bool:
        """Execute camera control command."""
        try:
            camera_thread = threading.Thread(target=self._open_camera_app)
            camera_thread.daemon = True
            camera_thread.start()
            return True
        except Exception as e:
            self.logger.error(f"Camera control failed: {e}")
            return False

    def _execute_money_detection(self) -> bool:
        """Execute money detection command."""
        try:
            detection_thread = threading.Thread(target=self._open_money_detection)
            detection_thread.daemon = True
            detection_thread.start()
            return True
        except Exception as e:
            self.logger.error(f"Money detection failed: {e}")
            return False

    def _execute_object_detection(self) -> bool:
        """Execute object detection command."""
        try:
            detection_thread = threading.Thread(target=self._open_object_detection)
            detection_thread.daemon = True
            detection_thread.start()
            return True
        except Exception as e:
            self.logger.error(f"Object detection failed: {e}")
            return False

    def _execute_system_control(self) -> bool:
        """Execute system control command (exit)."""
        self.speak("Thank you! Have a great day!")
        self.stop_listening()
        return True

    def _open_camera_app(self) -> None:
        """Open camera application in separate thread."""
        try:
            subprocess.Popen(['python', 'object_detection.py'])
            time.sleep(2)  # Brief wait for app to start
            self.speak("Object detection camera opened.")
        except Exception as e:
            self.logger.error(f"Failed to open camera app: {e}")
            self.speak("Sorry, I couldn't open the camera.")

    def _open_money_detection(self) -> None:
        """Open money detection application in separate thread."""
        try:
            subprocess.Popen(['python', 'money_detection.py'])
            time.sleep(2)  # Brief wait for app to start
            self.speak("Money detection camera opened.")
        except Exception as e:
            self.logger.error(f"Failed to open money detection: {e}")
            self.speak("Sorry, I couldn't open money detection.")

    def _open_object_detection(self) -> None:
        """Open object detection application in separate thread."""
        try:
            subprocess.Popen(['python', 'object_detection.py'])
            time.sleep(2)  # Brief wait for app to start
            self.speak("Object detection camera opened.")
        except Exception as e:
            self.logger.error(f"Failed to open object detection: {e}")
            self.speak("Sorry, I couldn't open object detection.")

    def speak(self, text: str) -> None:
        """
        Convert text to speech using the TTS engine.

        Args:
            text: Text to speak
        """
        if self.user_preferences.get("enable_voice_feedback", True):
            self.tts_engine.speak(text)

    def wish_user(self) -> None:
        """Greet the user based on time of day."""
        hour = datetime.datetime.now().hour

        if 0 <= hour < 12:
            greeting = "Good Morning!"
        elif 12 <= hour < 18:
            greeting = "Good Afternoon!"
        else:
            greeting = "Good Evening!"

        self.speak(greeting)
        self.speak("I am your enhanced voice assistant. How may I help you today?")

    def listen_for_commands(self) -> None:
        """Main listening loop for voice commands."""
        self.logger.info("Starting voice command listening loop")

        while self.listening_enabled:
            try:
                # Listen for speech input
                raw_text = self.speech_processor.listen_and_recognize(timeout=5)

                if raw_text and raw_text.lower() not in ['none', '']:
                    self.logger.info(f"Processing command: {raw_text}")
                    self.update_status(f"Processing: {raw_text[:30]}...")

                    success = self.process_voice_command(raw_text)

                    if not success:
                        self.speak("I didn't understand that. Could you please repeat?")

                    self.update_status("Listening...")
                else:
                    # Brief pause to prevent tight loop
                    time.sleep(0.1)

            except Exception as e:
                context = ErrorContext(
                    component="EnhancedVoiceAssistant",
                    operation="listen_for_commands",
                    session_id=self.current_session.session_id if self.current_session else None
                )
                self.error_handler.handle_error(e, context, ErrorSeverity.HIGH)

                # Brief pause before continuing
                time.sleep(1)

        self.logger.info("Voice command listening loop ended")

    def start_listening(self) -> None:
        """Start listening for voice commands."""
        if not self.listening_enabled:
            self.listening_enabled = True
            self.create_session()

            # Update UI
            if self.listen_button:
                self.listen_button.config(state=tk.DISABLED)
            if self.stop_button:
                self.stop_button.config(state=tk.NORMAL)
            self.update_status("Initializing...")

            # Start listening thread
            listen_thread = threading.Thread(target=self._start_listening_thread)
            listen_thread.daemon = True
            listen_thread.start()

    def _start_listening_thread(self) -> None:
        """Start the listening thread with proper initialization."""
        try:
            # Calibrate microphone
            calibrated = self.speech_processor.calibrate_microphone()
            if not calibrated:
                self.logger.warning("Microphone calibration failed")

            # Perform initial health check
            system_status = self.system_monitor.perform_health_check()
            if not system_status.is_system_healthy():
                self.logger.warning("System health check failed")

            # Greet user
            self.wish_user()

            # Update UI
            self.update_status("Listening...")

            # Start main listening loop
            self.listen_for_commands()

        except Exception as e:
            context = ErrorContext(
                component="EnhancedVoiceAssistant",
                operation="_start_listening_thread"
            )
            self.error_handler.handle_error(e, context, ErrorSeverity.CRITICAL)

    def stop_listening(self) -> None:
        """Stop listening for voice commands."""
        self.listening_enabled = False
        self.end_session()

        # Update UI
        if self.listen_button:
            self.listen_button.config(state=tk.NORMAL)
        if self.stop_button:
            self.stop_button.config(state=tk.DISABLED)
        self.update_status("Not Listening")

        self.logger.info("Voice assistant stopped")

    def update_status(self, status: str) -> None:
        """Update the status display."""
        if self.status_label:
            self.status_label.config(text=status)

        # Update stats display if available
        if self.stats_label:
            stats_text = f"Commands: {self.stats.total_commands} | Success: {self.stats.successful_commands}"
            self.stats_label.config(text=stats_text)

    def create_gui(self) -> tk.Tk:
        """Create the graphical user interface."""
        self.root = tk.Tk()
        self.root.title("Enhanced Voice Assistant")
        self.root.geometry("500x300")
        self.root.resizable(True, True)

        # Create main frame
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = tk.Label(
            main_frame,
            text="Enhanced Voice Assistant",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 20))

        # Control buttons
        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=(0, 20))

        self.listen_button = tk.Button(
            button_frame,
            text="Start Listening",
            command=self.start_listening,
            bg="green",
            fg="white",
            font=("Arial", 12),
            width=15
        )
        self.listen_button.pack(side=tk.LEFT, padx=(0, 10))

        self.stop_button = tk.Button(
            button_frame,
            text="Stop Listening",
            command=self.stop_listening,
            bg="red",
            fg="white",
            font=("Arial", 12),
            width=15,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT)

        # Status display
        status_frame = tk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(0, 10))

        status_title = tk.Label(status_frame, text="Status:", font=("Arial", 10, "bold"))
        status_title.pack(anchor=tk.W)

        self.status_label = tk.Label(
            status_frame,
            text="Not Listening",
            font=("Arial", 10),
            wraplength=400,
            justify=tk.LEFT
        )
        self.status_label.pack(anchor=tk.W, fill=tk.X)

        # Statistics display
        stats_frame = tk.Frame(main_frame)
        stats_frame.pack(fill=tk.X, pady=(10, 0))

        stats_title = tk.Label(stats_frame, text="Statistics:", font=("Arial", 10, "bold"))
        stats_title.pack(anchor=tk.W)

        self.stats_label = tk.Label(
            stats_frame,
            text="Commands: 0 | Success: 0",
            font=("Arial", 10)
        )
        self.stats_label.pack(anchor=tk.W)

        # Health check button
        health_button = tk.Button(
            main_frame,
            text="System Health Check",
            command=self._perform_health_check_gui
        )
        health_button.pack(pady=(20, 0))

        return self.root

    def _perform_health_check_gui(self) -> None:
        """Perform health check and display results in GUI."""
        try:
            status = self.system_monitor.perform_health_check()

            health_info = f"""
System Health Check:
Voice Engine: {'✓' if status.is_voice_engine_active else '✗'}
Microphone: {'✓' if status.is_microphone_active else '✗'}
Camera: {'✓' if status.is_camera_active else '✗'}
Memory Usage: {status.memory_usage_mb:.1f} MB
CPU Usage: {status.cpu_usage_percent:.1f}%
Last Check: {format_timestamp(status.last_health_check)}
            """.strip()

            # Show results in a message box
            import tkinter.messagebox as messagebox
            messagebox.showinfo("System Health", health_info)

        except Exception as e:
            self.logger.error(f"Health check GUI failed: {e}")
            import tkinter.messagebox as messagebox
            messagebox.showerror("Error", f"Health check failed: {e}")

    def run(self) -> None:
        """Run the voice assistant application."""
        try:
            # Create GUI
            root = self.create_gui()

            # Set up cleanup on window close
            root.protocol("WM_DELETE_WINDOW", self._on_closing)

            # Start the GUI event loop
            self.logger.info("Starting GUI event loop")
            root.mainloop()

        except Exception as e:
            context = ErrorContext(
                component="EnhancedVoiceAssistant",
                operation="run"
            )
            self.error_handler.handle_error(e, context, ErrorSeverity.CRITICAL)
            raise

    def _on_closing(self) -> None:
        """Handle application closing."""
        self.logger.info("Application closing")

        # Stop listening if active
        if self.listening_enabled:
            self.stop_listening()

        # Save final statistics
        try:
            self.data_manager.save_statistics(self.stats)
        except Exception as e:
            self.logger.error(f"Failed to save final statistics: {e}")

        # Destroy GUI
        if self.root:
            self.root.destroy()


def main():
    """Main entry point for the enhanced voice assistant."""
    try:
        # Create and run the assistant
        assistant = EnhancedVoiceAssistant()
        assistant.run()

    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
    except Exception as e:
        print(f"Critical error: {e}")
        raise


if __name__ == "__main__":
    main()
