import json
import os
import shutil
from datetime import datetime, timedelta
import uuid

HISTORY_FILE = "chat_history.json"

def load_chat_history(user_id=None):
    """Loads chat history, filters by user_id and 7-day retention."""
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
                # Filter by user_id if provided
                if user_id:
                    if session.get("user_id") == user_id:
                        valid_sessions.append(session)
                else:
                    valid_sessions.append(session)
        except (ValueError, KeyError):
            continue
            
    # Sort by timestamp descending (newest first)
    valid_sessions.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return valid_sessions

def group_chat_history(sessions):
    """Groups sessions into Today, Yesterday, and Previous 7 Days."""
    grouped = {
        "Today": [],
        "Yesterday": [],
        "Previous 7 Days": []
    }
    
    now = datetime.now().date()
    yesterday = now - timedelta(days=1)
    
    for session in sessions:
        try:
            session_ts = datetime.fromisoformat(session["timestamp"])
            session_date = session_ts.date()
            
            if session_date == now:
                grouped["Today"].append(session)
            elif session_date == yesterday:
                grouped["Yesterday"].append(session)
            else:
                grouped["Previous 7 Days"].append(session)
        except ValueError:
            continue
            
    return grouped

def save_chat_session(session_id, messages, user_id=None, title=None):
    """Saves or updates a chat session."""
    if not os.path.exists(HISTORY_FILE):
        sessions = []
    else:
        try:
            with open(HISTORY_FILE, "r") as f:
                data = json.load(f)
                sessions = data.get("sessions", [])
        except (json.JSONDecodeError, IOError):
            sessions = []
    
    existing_session = next((s for s in sessions if s["id"] == session_id), None)
    timestamp = datetime.now().isoformat()
    
    if not title and messages:
        first_user_msg = next((m for m in messages if m["role"] == "user"), None)
        if first_user_msg:
            clean_content = first_user_msg["content"][:35].strip()
            title = clean_content + "..." if len(first_user_msg["content"]) > 35 else clean_content
        else:
            title = "New Chat"
    elif not title:
        title = "New Chat"

    if existing_session:
        existing_session["messages"] = messages
        existing_session["timestamp"] = timestamp
        if existing_session["title"] == "New Chat" and title != "New Chat":
             existing_session["title"] = title
        if user_id and "user_id" not in existing_session:
             existing_session["user_id"] = user_id
    else:
        new_session = {
            "id": session_id,
            "user_id": user_id,
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
    """Deletes chat session from JSON and removes associated vector store."""
    # 1. Remove from JSON
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                data = json.load(f)
                sessions = data.get("sessions", [])
            
            sessions = [s for s in sessions if s["id"] != session_id]
            
            with open(HISTORY_FILE, "w") as f:
                json.dump({"sessions": sessions}, f, indent=4)
        except (json.JSONDecodeError, IOError):
            pass

    # 2. Remove specific Vector Store folder
    index_path = f"faiss_indexes/{session_id}"
    if os.path.exists(index_path):
        try:
            shutil.rmtree(index_path)
        except OSError:
            pass