"""
utils/user_data.py
Simple JSON-based user management (register / login).
"""

import json, os, hashlib

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "users.json")


def _load():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE) as f:
        return json.load(f)


def _save(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _hash(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


def register(username, password):
    """Returns (True, msg) on success, (False, msg) on fail."""
    if not username.strip() or not password.strip():
        return False, "Username and password cannot be empty."
    db = _load()
    if username.lower() in db:
        return False, "Username already exists."
    db[username.lower()] = {"pw": _hash(password), "history": []}
    _save(db)
    return True, "Account created successfully!"


def login(username, password):
    """Returns (True, msg) on success, (False, msg) on fail."""
    db = _load()
    user = db.get(username.lower())
    if not user:
        return False, "User not found."
    if user["pw"] != _hash(password):
        return False, "Incorrect password."
    return True, "Login successful!"


def save_history(username: str, entry: str):
    """Append a translation entry to the user's history."""
    if not username: username = "Guest"
    db = _load()
    key = username.lower()
    
    # Auto-initialize user if not present (helps with Guest account)
    if key not in db:
        db[key] = {"pw": None, "history": []}
        
    db[key].setdefault("history", []).append(entry)
    
    # Cap at 100 entries
    if len(db[key]["history"]) > 100:
        db[key]["history"] = db[key]["history"][-100:]
        
    _save(db)


def get_history(username: str):
    if not username: username = "Guest"
    db = _load()
    user = db.get(username.lower(), {"history": []})
    return user.get("history", [])


def clear_history(username: str):
    """Delete all history for a user."""
    if not username: username = "Guest"
    db = _load()
    key = username.lower()
    if key in db:
        db[key]["history"] = []
        _save(db)
        return True
    return False


def delete_history_item(username: str, item_id: int):
    """Delete a single history entry for a user by index."""
    if not username: username = "Guest"
    db = _load()
    key = username.lower()
    if key in db:
        history = db[key].get("history", [])
        if 0 <= item_id < len(history):
            history.pop(item_id)
            db[key]["history"] = history
            _save(db)
            return True
    return False
