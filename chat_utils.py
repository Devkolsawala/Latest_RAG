import json
import os
from datetime import datetime, timedelta
import uuid

HISTORY_FILE = "chat_history.json"

def load_chat_history():
    """Loads chat history from JSON file, filtering out sessions older than 7 days."""
    if not os.path.exists(HISTORY_FILE):
        return []

    try:
        with open(HISTORY_FILE, "r") as f:
            data = json.load(f)
            sessions = data.get("sessions", [])
    except (json.JSONDecodeError, IOError):
        return []

    # Filter sessions older than 7 days
    seven_days_ago = datetime.now() - timedelta(days=7)
    valid_sessions = []
    
    for session in sessions:
        try:
            session_date = datetime.fromisoformat(session["timestamp"])
            if session_date > seven_days_ago:
                valid_sessions.append(session)
        except (ValueError, KeyError):
            continue
            
    # Sort by timestamp descending (newest first)
    valid_sessions.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return valid_sessions

def save_chat_session(session_id, messages, title=None):
    """Saves or updates a chat session."""
    sessions = load_chat_history()
    
    # Check if session exists
    existing_session = next((s for s in sessions if s["id"] == session_id), None)
    
    timestamp = datetime.now().isoformat()
    
    if not title and messages:
        # Generate simple title from first user message if not provided
        first_user_msg = next((m for m in messages if m["role"] == "user"), None)
        if first_user_msg:
            title = first_user_msg["content"][:30] + "..."
        else:
            title = "New Chat"
    elif not title:
        title = "New Chat"

    if existing_session:
        existing_session["messages"] = messages
        existing_session["timestamp"] = timestamp # Update timestamp on new activity
        # Keep existing title unless specifically updated logic (omitted for simplicity)
    else:
        new_session = {
            "id": session_id,
            "timestamp": timestamp,
            "title": title,
            "messages": messages
        }
        sessions.insert(0, new_session)
    
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump({"sessions": sessions}, f, indent=4)
    except IOError:
        pass

def get_new_session_id():
    return str(uuid.uuid4())

def delete_chat_session(session_id):
    sessions = load_chat_history()
    sessions = [s for s in sessions if s["id"] != session_id]
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump({"sessions": sessions}, f, indent=4)
    except IOError:
        pass
