"""
Speech processing and NLP features for the Voice Assistant.
This module handles advanced speech recognition, text processing, and command interpretation.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict
import speech_recognition as sr
import pyttsx3
from difflib import SequenceMatcher
from models import VoiceCommand, VoiceCommandType, AudioConfig
from utils import timing_decorator, parse_voice_command


class SpeechProcessor:
    """
    Advanced speech processing and command interpretation.
    Handles speech recognition, text processing, and command classification.
    """

    def __init__(self, audio_config: AudioConfig):
        """
        Initialize the speech processor.

        Args:
            audio_config: Audio configuration settings
        """
        self.config = audio_config
        self.logger = logging.getLogger("voice_assistant.speech_processor")

        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = self.config.pause_threshold
        self.recognizer.energy_threshold = self.config.energy_threshold
        self.recognizer.dynamic_energy_threshold = self.config.dynamic_energy_threshold

        # Command patterns and keywords
        self.command_patterns = self._initialize_command_patterns()
        self.synonym_map = self._initialize_synonyms()

        # Processing statistics
        self.processing_stats = {
            "total_commands": 0,
            "successful_recognitions": 0,
            "failed_recognitions": 0,
            "average_confidence": 0.0
        }

    def _initialize_command_patterns(self) -> Dict[str, List[str]]:
        """
        Initialize command patterns for different voice commands.

        Returns:
            Dictionary mapping command types to pattern lists
        """
        return {
            "wikipedia_search": [
                r"search (?:on |for )?wikipedia (?:for )?(.*)",
                r"what is (.+)",
                r"tell me about (.+)",
                r"who is (.+)",
                r"define (.+)"
            ],
            "youtube_search": [
                r"search (?:on |for )?youtube (?:for )?(.*)",
                r"find (?:videos? |)(?:on |about )(.+) on youtube"
            ],
            "youtube_play": [
                r"play (.+) on youtube",
                r"play (.+) video",
                r"start (.+) video"
            ],
            "web_browser": [
                r"open (.+)",
                r"launch (.+)",
                r"go to (.+)",
                r"visit (.+)"
            ],
            "time_query": [
                r"what time is it",
                r"what's the time",
                r"tell me the time",
                r"current time"
            ],
            "joke": [
                r"tell me a joke",
                r"say a joke",
                r"make me laugh",
                r"joke please"
            ],
            "camera_control": [
                r"open camera",
                r"start camera",
                r"turn on camera",
                r"activate camera"
            ],
            "money_detection": [
                r"scan money",
                r"detect money",
                r"identify money",
                r"check money"
            ],
            "object_detection": [
                r"detect objects",
                r"scan objects",
                r"identify objects",
                r"what do you see"
            ],
            "system_control": [
                r"exit",
                r"quit",
                r"stop",
                r"goodbye",
                r"bye"
            ]
        }

    def _initialize_synonyms(self) -> Dict[str, List[str]]:
        """
        Initialize synonym mappings for better command recognition.

        Returns:
            Dictionary mapping words to their synonyms
        """
        return {
            "google": ["google", "search engine", "web search"],
            "youtube": ["youtube", "yt", "video"],
            "wikipedia": ["wikipedia", "wiki", "encyclopedia"],
            "camera": ["camera", "webcam", "video camera"],
            "money": ["money", "currency", "rupees", "cash", "notes"],
            "object": ["object", "thing", "item", "stuff"]
        }

    @timing_decorator
    def listen_and_recognize(self, timeout: int = 5) -> Optional[str]:
        """
        Listen for speech input and convert to text.

        Args:
            timeout: Maximum time to wait for speech input

        Returns:
            Recognized text or None if recognition failed
        """
        try:
            with sr.Microphone() as source:
                self.logger.debug("Listening for speech input...")
                audio = self.recognizer.listen(source, timeout=timeout)

                self.logger.debug("Processing speech recognition...")
                text = self.recognizer.recognize_google(audio, language='en-in')

                self.processing_stats["total_commands"] += 1
                self.processing_stats["successful_recognitions"] += 1

                self.logger.info(f"Recognized: {text}")
                return text

        except sr.WaitTimeoutError:
            self.logger.warning("Speech recognition timeout")
        except sr.UnknownValueError:
            self.logger.warning("Could not understand audio")
        except sr.RequestError as e:
            self.logger.error(f"Speech recognition service error: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error in speech recognition: {e}")

        self.processing_stats["total_commands"] += 1
        self.processing_stats["failed_recognitions"] += 1
        return None

    def parse_command(self, text: str) -> VoiceCommand:
        """
        Parse recognized text into a structured voice command.

        Args:
            text: Raw recognized text

        Returns:
            Parsed VoiceCommand object
        """
        if not text or not text.strip():
            return VoiceCommand(
                command_type=VoiceCommandType.SYSTEM_CONTROL,
                raw_text=text or "",
                confidence_score=0.0
            )

        # Normalize text
        normalized_text = self._normalize_text(text)

        # Try to match against command patterns
        best_match = self._find_best_command_match(normalized_text)

        if best_match:
            command_type, parameters, confidence = best_match
            return VoiceCommand(
                command_type=command_type,
                raw_text=text,
                parsed_parameters=parameters,
                confidence_score=confidence
            )

        # Fallback to basic parsing
        basic_parse = parse_voice_command(text)
        command_type = self._infer_command_type(basic_parse)

        return VoiceCommand(
            command_type=command_type,
            raw_text=text,
            parsed_parameters=basic_parse,
            confidence_score=0.5  # Default confidence for basic parsing
        )

    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for better pattern matching.

        Args:
            text: Raw text to normalize

        Returns:
            Normalized text
        """
        # Convert to lowercase
        normalized = text.lower().strip()

        # Expand contractions
        contractions = {
            "what's": "what is",
            "it's": "it is",
            "don't": "do not",
            "can't": "cannot",
            "won't": "will not",
            "i'm": "i am",
            "you're": "you are",
            "we're": "we are",
            "they're": "they are"
        }

        for contraction, expansion in contractions.items():
            normalized = normalized.replace(contraction, expansion)

        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)

        return normalized

    def _find_best_command_match(self, text: str) -> Optional[Tuple[VoiceCommandType, Dict[str, Any], float]]:
        """
        Find the best matching command pattern for the given text.

        Args:
            text: Normalized text to match

        Returns:
            Tuple of (command_type, parameters, confidence) or None
        """
        best_match = None
        best_confidence = 0.0

        for command_type_str, patterns in self.command_patterns.items():
            command_type = VoiceCommandType(command_type_str)

            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    # Calculate confidence based on pattern specificity
                    confidence = self._calculate_pattern_confidence(pattern, match, text)

                    if confidence > best_confidence:
                        parameters = self._extract_parameters(match, command_type)
                        best_match = (command_type, parameters, confidence)
                        best_confidence = confidence

        return best_match

    def _calculate_pattern_confidence(self, pattern: str, match: re.Match, text: str) -> float:
        """
        Calculate confidence score for a pattern match.

        Args:
            pattern: Regex pattern used for matching
            match: Regex match object
            text: Original text

        Returns:
            Confidence score between 0 and 1
        """
        # Base confidence from pattern complexity
        pattern_complexity = len(pattern.split()) / 10.0  # Normalize by expected max

        # Match coverage (how much of the text was matched)
        matched_length = len(match.group(0))
        total_length = len(text)
        coverage = matched_length / total_length if total_length > 0 else 0

        # Keyword presence bonus
        keyword_bonus = 0.0
        keywords = ["search", "play", "open", "show", "detect", "scan"]
        if any(keyword in text for keyword in keywords):
            keyword_bonus = 0.2

        confidence = min(1.0, pattern_complexity + coverage + keyword_bonus)
        return confidence

    def _extract_parameters(self, match: re.Match, command_type: VoiceCommandType) -> Dict[str, Any]:
        """
        Extract parameters from a regex match.

        Args:
            match: Regex match object
            command_type: Type of command being processed

        Returns:
            Dictionary of extracted parameters
        """
        parameters = {}

        if match.groups():
            if command_type == VoiceCommandType.WIKIPEDIA_SEARCH:
                parameters["query"] = match.group(1).strip()
            elif command_type in [VoiceCommandType.YOUTUBE_SEARCH, VoiceCommandType.YOUTUBE_PLAY]:
                parameters["query"] = match.group(1).strip()
            elif command_type == VoiceCommandType.WEB_BROWSER:
                target = match.group(1).strip().lower()
                parameters["target"] = self._resolve_synonym(target)

        return parameters

    def _resolve_synonym(self, word: str) -> str:
        """
        Resolve a word to its canonical form using synonym mapping.

        Args:
            word: Word to resolve

        Returns:
            Canonical form of the word
        """
        for canonical, synonyms in self.synonym_map.items():
            if word in synonyms:
                return canonical
        return word

    def _infer_command_type(self, basic_parse: Dict[str, Any]) -> VoiceCommandType:
        """
        Infer command type from basic parsing results.

        Args:
            basic_parse: Basic parsing results

        Returns:
            Inferred command type
        """
        action = basic_parse.get("action")
        target = basic_parse.get("target")

        if action == "search" and target == "wikipedia":
            return VoiceCommandType.WIKIPEDIA_SEARCH
        elif action == "search" and target == "youtube":
            return VoiceCommandType.YOUTUBE_SEARCH
        elif action == "play":
            return VoiceCommandType.YOUTUBE_PLAY
        elif action == "open":
            return VoiceCommandType.WEB_BROWSER
        elif action == "detect" and target == "money":
            return VoiceCommandType.MONEY_DETECTION
        elif action == "detect" and target == "object":
            return VoiceCommandType.OBJECT_DETECTION
        elif action == "show" and "time" in basic_parse.get("original_text", "").lower():
            return VoiceCommandType.TIME_QUERY
        elif "joke" in basic_parse.get("original_text", "").lower():
            return VoiceCommandType.JOKE
        elif "camera" in basic_parse.get("original_text", "").lower():
            return VoiceCommandType.CAMERA_CONTROL
        else:
            return VoiceCommandType.SYSTEM_CONTROL

    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get current processing statistics.

        Returns:
            Dictionary with processing statistics
        """
        stats = self.processing_stats.copy()
        if stats["total_commands"] > 0:
            stats["success_rate"] = stats["successful_recognitions"] / stats["total_commands"]
        else:
            stats["success_rate"] = 0.0
        return stats

    def calibrate_microphone(self, duration: int = 1) -> bool:
        """
        Calibrate microphone for ambient noise.

        Args:
            duration: Duration to listen for ambient noise

        Returns:
            True if calibration successful, False otherwise
        """
        try:
            with sr.Microphone() as source:
                self.logger.info("Calibrating microphone for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=duration)
                self.logger.info("Microphone calibration complete")
                return True
        except Exception as e:
            self.logger.error(f"Microphone calibration failed: {e}")
            return False


class TextToSpeechEngine:
    """
    Enhanced text-to-speech engine with voice customization.
    """

    def __init__(self, voice_config: Dict[str, Any]):
        """
        Initialize the TTS engine.

        Args:
            voice_config: Voice configuration settings
        """
        self.config = voice_config
        self.logger = logging.getLogger("voice_assistant.tts")

        try:
            self.engine = pyttsx3.init(self.config.get("engine", "sapi5"))
            self._configure_voice()
        except Exception as e:
            self.logger.error(f"Failed to initialize TTS engine: {e}")
            self.engine = None

    def _configure_voice(self) -> None:
        """Configure voice settings."""
        if not self.engine:
            return

        try:
            # Set voice properties
            voices = self.engine.getProperty('voices')
            if voices:
                self.engine.setProperty('voice', voices[0].id)

            self.engine.setProperty('rate', self.config.get("rate", 200))
            self.engine.setProperty('volume', self.config.get("volume", 0.8))

        except Exception as e:
            self.logger.warning(f"Could not configure voice properties: {e}")

    def speak(self, text: str) -> bool:
        """
        Convert text to speech.

        Args:
            text: Text to speak

        Returns:
            True if speech was successful, False otherwise
        """
        if not self.engine or not text:
            return False

        try:
            self.engine.say(text)
            self.engine.runAndWait()
            return True
        except Exception as e:
            self.logger.error(f"TTS error: {e}")
            return False

    def speak_async(self, text: str) -> None:
        """
        Convert text to speech asynchronously.

        Args:
            text: Text to speak
        """
        import threading

        def speak_thread():
            self.speak(text)

        thread = threading.Thread(target=speak_thread)
        thread.daemon = True
        thread.start()

    def get_available_voices(self) -> List[Dict[str, Any]]:
        """
        Get list of available voices.

        Returns:
            List of voice information dictionaries
        """
        if not self.engine:
            return []

        try:
            voices = self.engine.getProperty('voices')
            return [
                {
                    "id": voice.id,
                    "name": voice.name,
                    "age": getattr(voice, 'age', None),
                    "gender": getattr(voice, 'gender', None)
                }
                for voice in voices
            ]
        except Exception as e:
            self.logger.error(f"Could not get voice list: {e}")
            return []

    def stop_speaking(self) -> None:
        """Stop current speech output."""
        if self.engine:
            try:
                self.engine.stop()
            except Exception as e:
                self.logger.warning(f"Could not stop speech: {e}")
