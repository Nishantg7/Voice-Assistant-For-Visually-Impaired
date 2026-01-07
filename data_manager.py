"""
Data persistence layer for the Voice Assistant application.
Handles file operations, session storage, and configuration management.
"""

import json
import csv
import sqlite3
import os
import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import asdict
from models import SessionData, VoiceCommand, DetectionResult, ProcessingStats
from utils import safe_file_operation, timing_decorator


class DataManager:
    """
    Manages data persistence operations including sessions, configurations, and statistics.
    """

    def __init__(self, data_dir: str = "data"):
        """
        Initialize the data manager.

        Args:
            data_dir: Directory for storing data files
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        self.logger = logging.getLogger("voice_assistant.data_manager")

        # Initialize database paths
        self.db_path = self.data_dir / "voice_assistant.db"
        self.sessions_file = self.data_dir / "sessions.json"
        self.config_file = self.data_dir / "config.json"
        self.stats_file = self.data_dir / "statistics.json"

        # Initialize database
        self._init_database()

    @safe_file_operation
    def _init_database(self) -> None:
        """Initialize the SQLite database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Create sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    is_active INTEGER DEFAULT 1,
                    total_duration REAL DEFAULT 0.0,
                    command_count INTEGER DEFAULT 0,
                    detection_count INTEGER DEFAULT 0
                )
            ''')

            # Create commands table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS commands (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    command_type TEXT NOT NULL,
                    raw_text TEXT NOT NULL,
                    confidence_score REAL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id)
                )
            ''')

            # Create detections table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    object_class TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    bounding_box TEXT,
                    timestamp TEXT NOT NULL
                )
            ''')

            # Create statistics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_stats (
                    date TEXT PRIMARY KEY,
                    total_commands INTEGER DEFAULT 0,
                    successful_commands INTEGER DEFAULT 0,
                    total_detections INTEGER DEFAULT 0,
                    average_processing_time REAL DEFAULT 0.0
                )
            ''')

            conn.commit()
            self.logger.info("Database initialized successfully")

    @timing_decorator
    def save_session(self, session: SessionData) -> bool:
        """
        Save a session to the database.

        Args:
            session: Session data to save

        Returns:
            True if save was successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Insert or replace session
                cursor.execute('''
                    INSERT OR REPLACE INTO sessions
                    (session_id, start_time, end_time, is_active, total_duration,
                     command_count, detection_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session.session_id,
                    session.start_time.isoformat(),
                    None if session.is_active else (session.start_time + timedelta(seconds=session.total_duration)).isoformat(),
                    1 if session.is_active else 0,
                    session.total_duration,
                    len(session.commands_processed),
                    len(session.detections_made)
                ))

                # Insert commands
                for command in session.commands_processed:
                    cursor.execute('''
                        INSERT INTO commands
                        (session_id, command_type, raw_text, confidence_score, timestamp)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        session.session_id,
                        command.command_type.value,
                        command.raw_text,
                        command.confidence_score,
                        command.timestamp.isoformat()
                    ))

                # Insert detections
                for detection in session.detections_made:
                    cursor.execute('''
                        INSERT INTO detections
                        (session_id, object_class, confidence, bounding_box, timestamp)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        session.session_id,
                        detection.object_class,
                        detection.confidence,
                        str(detection.bounding_box) if detection.bounding_box else None,
                        detection.timestamp.isoformat()
                    ))

                conn.commit()
                self.logger.info(f"Session {session.session_id} saved successfully")
                return True

        except Exception as e:
            self.logger.error(f"Failed to save session {session.session_id}: {e}")
            return False

    def load_session(self, session_id: str) -> Optional[SessionData]:
        """
        Load a session from the database.

        Args:
            session_id: ID of the session to load

        Returns:
            SessionData object or None if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Load session data
                cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
                session_row = cursor.fetchone()

                if not session_row:
                    return None

                session = SessionData(
                    session_id=session_row[0],
                    start_time=datetime.fromisoformat(session_row[1]),
                    is_active=bool(session_row[3]),
                    total_duration=session_row[4]
                )

                # Load commands
                cursor.execute("SELECT * FROM commands WHERE session_id = ?", (session_id,))
                command_rows = cursor.fetchall()

                for row in command_rows:
                    from models import VoiceCommandType
                    command = VoiceCommand(
                        command_type=VoiceCommandType(row[2]),
                        raw_text=row[3],
                        confidence_score=row[4],
                        timestamp=datetime.fromisoformat(row[5])
                    )
                    session.commands_processed.append(command)

                # Load detections
                cursor.execute("SELECT * FROM detections WHERE session_id = ?", (session_id,))
                detection_rows = cursor.fetchall()

                for row in detection_rows:
                    detection = DetectionResult(
                        object_class=row[2],
                        confidence=row[3],
                        bounding_box=eval(row[4]) if row[4] else None,
                        timestamp=datetime.fromisoformat(row[5])
                    )
                    session.detections_made.append(detection)

                return session

        except Exception as e:
            self.logger.error(f"Failed to load session {session_id}: {e}")
            return None

    def get_recent_sessions(self, limit: int = 10) -> List[SessionData]:
        """
        Get a list of recent sessions.

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of recent SessionData objects
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT session_id FROM sessions ORDER BY start_time DESC LIMIT ?",
                    (limit,)
                )
                session_ids = [row[0] for row in cursor.fetchall()]

                sessions = []
                for session_id in session_ids:
                    session = self.load_session(session_id)
                    if session:
                        sessions.append(session)

                return sessions

        except Exception as e:
            self.logger.error(f"Failed to get recent sessions: {e}")
            return []

    @safe_file_operation
    def save_config(self, config: Dict[str, Any]) -> bool:
        """
        Save configuration to file.

        Args:
            config: Configuration dictionary to save

        Returns:
            True if save was successful, False otherwise
        """
        try:
            config_data = {
                "config": config,
                "last_updated": datetime.now().isoformat(),
                "version": "1.0"
            }

            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2, default=str)

            self.logger.info("Configuration saved successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            return False

    def load_config(self) -> Optional[Dict[str, Any]]:
        """
        Load configuration from file.

        Returns:
            Configuration dictionary or None if not found
        """
        try:
            if not self.config_file.exists():
                return None

            with open(self.config_file, 'r') as f:
                data = json.load(f)

            return data.get("config", {})

        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            return None

    @timing_decorator
    def save_statistics(self, stats: ProcessingStats) -> bool:
        """
        Save processing statistics.

        Args:
            stats: Statistics to save

        Returns:
            True if save was successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                today = stats.last_updated.strftime("%Y-%m-%d")

                cursor.execute('''
                    INSERT OR REPLACE INTO daily_stats
                    (date, total_commands, successful_commands, total_detections,
                     average_processing_time)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    today,
                    stats.total_commands,
                    stats.successful_commands,
                    stats.total_detections,
                    stats.average_processing_time
                ))

                conn.commit()

                # Also save to JSON file for backward compatibility
                stats_dict = asdict(stats)
                stats_dict["last_updated"] = stats.last_updated.isoformat()

                with open(self.stats_file, 'w') as f:
                    json.dump(stats_dict, f, indent=2)

                self.logger.info("Statistics saved successfully")
                return True

        except Exception as e:
            self.logger.error(f"Failed to save statistics: {e}")
            return False

    def load_statistics(self, date: Optional[str] = None) -> Optional[ProcessingStats]:
        """
        Load processing statistics.

        Args:
            date: Specific date to load (YYYY-MM-DD), or None for today

        Returns:
            ProcessingStats object or None if not found
        """
        try:
            target_date = date or datetime.now().strftime("%Y-%m-%d")

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM daily_stats WHERE date = ?", (target_date,))
                row = cursor.fetchone()

                if row:
                    return ProcessingStats(
                        total_commands=row[1],
                        successful_commands=row[2],
                        total_detections=row[3],
                        average_processing_time=row[4],
                        last_updated=datetime.fromisoformat(target_date + "T00:00:00")
                    )

                # Fallback to JSON file
                if self.stats_file.exists():
                    with open(self.stats_file, 'r') as f:
                        data = json.load(f)
                        return ProcessingStats(**data)

                return None

        except Exception as e:
            self.logger.error(f"Failed to load statistics: {e}")
            return None

    def export_sessions_to_csv(self, output_file: str, date_range: Optional[tuple] = None) -> bool:
        """
        Export session data to CSV file.

        Args:
            output_file: Path to output CSV file
            date_range: Optional tuple of (start_date, end_date) in YYYY-MM-DD format

        Returns:
            True if export was successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                query = """
                    SELECT s.session_id, s.start_time, s.end_time, s.total_duration,
                           s.command_count, s.detection_count, s.is_active
                    FROM sessions s
                """

                params = []
                if date_range:
                    query += " WHERE DATE(s.start_time) BETWEEN ? AND ?"
                    params = date_range

                query += " ORDER BY s.start_time DESC"

                cursor.execute(query, params)
                sessions = cursor.fetchall()

                with open(output_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        'Session ID', 'Start Time', 'End Time', 'Duration (s)',
                        'Command Count', 'Detection Count', 'Is Active'
                    ])

                    for session in sessions:
                        writer.writerow(session)

                self.logger.info(f"Exported {len(sessions)} sessions to {output_file}")
                return True

        except Exception as e:
            self.logger.error(f"Failed to export sessions to CSV: {e}")
            return False

    def cleanup_old_data(self, days_to_keep: int = 30) -> int:
        """
        Clean up old session data.

        Args:
            days_to_keep: Number of days of data to keep

        Returns:
            Number of sessions cleaned up
        """
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Delete old sessions and related data
                cursor.execute("DELETE FROM detections WHERE session_id IN (SELECT session_id FROM sessions WHERE start_time < ?)", (cutoff_date,))
                cursor.execute("DELETE FROM commands WHERE session_id IN (SELECT session_id FROM sessions WHERE start_time < ?)", (cutoff_date,))
                cursor.execute("DELETE FROM sessions WHERE start_time < ?", (cutoff_date,))

                deleted_count = cursor.rowcount
                conn.commit()

                self.logger.info(f"Cleaned up {deleted_count} old sessions")
                return deleted_count

        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")
            return 0

    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Dictionary with database statistics
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                stats = {}

                # Count records in each table
                tables = ['sessions', 'commands', 'detections', 'daily_stats']
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    stats[f"{table}_count"] = cursor.fetchone()[0]

                # Get database file size
                stats["database_size_bytes"] = os.path.getsize(self.db_path) if self.db_path.exists() else 0

                # Get date range
                cursor.execute("SELECT MIN(start_time), MAX(start_time) FROM sessions")
                date_range = cursor.fetchone()
                stats["date_range"] = date_range if date_range[0] else None

                return stats

        except Exception as e:
            self.logger.error(f"Failed to get database stats: {e}")
            return {}
