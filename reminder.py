import json
import os
from datetime import datetime

class ReminderManager:
    def __init__(self, notes_file="notes.json"):
        self.notes_file = notes_file
        self.ensure_notes_file()

    def ensure_notes_file(self):
        """Create notes file if it doesn't exist"""
        if not os.path.exists(self.notes_file):
            with open(self.notes_file, 'w') as f:
                json.dump([], f)

    def add_note(self, content):
        """Add a new note/reminder"""
        try:
            with open(self.notes_file, 'r') as f:
                notes = json.load(f)

            note = {
                'id': len(notes) + 1,
                'content': content,
                'timestamp': datetime.now().isoformat(),
                'type': 'note'
            }

            notes.append(note)

            with open(self.notes_file, 'w') as f:
                json.dump(notes, f, indent=2)

            return f"Note saved: {content}"

        except Exception as e:
            return f"Error saving note: {str(e)}"

    def get_all_notes(self):
        """Retrieve all saved notes"""
        try:
            with open(self.notes_file, 'r') as f:
                notes = json.load(f)

            if not notes:
                return "You have no saved notes."

            response = "Here are your notes:\n"
            for i, note in enumerate(notes, 1):
                response += f"{i}. {note['content']}\n"

            return response

        except Exception as e:
            return f"Error retrieving notes: {str(e)}"

    def clear_notes(self):
        """Clear all notes"""
        try:
            with open(self.notes_file, 'w') as f:
                json.dump([], f)
            return "All notes have been cleared."
        except Exception as e:
            return f"Error clearing notes: {str(e)}"

    def search_notes(self, keyword):
        """Search notes containing a specific keyword"""
        try:
            with open(self.notes_file, 'r') as f:
                notes = json.load(f)

            matching_notes = [note for note in notes if keyword.lower() in note['content'].lower()]

            if not matching_notes:
                return f"No notes found containing '{keyword}'."

            response = f"Notes containing '{keyword}':\n"
            for i, note in enumerate(matching_notes, 1):
                response += f"{i}. {note['content']}\n"

            return response

        except Exception as e:
            return f"Error searching notes: {str(e)}"

def save_note(content):
    """Simple function to save a note"""
    manager = ReminderManager()
    return manager.add_note(content)

def get_notes():
    """Simple function to get all notes"""
    manager = ReminderManager()
    return manager.get_all_notes()

def clear_all_notes():
    """Simple function to clear all notes"""
    manager = ReminderManager()
    return manager.clear_notes()

def find_notes(keyword):
    """Simple function to search notes"""
    manager = ReminderManager()
    return manager.search_notes(keyword)

if __name__ == "__main__":
    # Test the reminder functions
    print(save_note("Buy groceries"))
    print(save_note("Call mom"))
    print(get_notes())
    print(find_notes("buy"))
