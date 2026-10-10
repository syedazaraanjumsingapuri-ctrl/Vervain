"""Simple register/login. Users and their progress are saved in user_data/users.json."""
import hashlib
import json
import os
from pathlib import Path

DIR = Path(__file__).parent / "user_data"
DIR.mkdir(exist_ok=True)
FILE = DIR / "users.json"


def _load():
    return json.loads(FILE.read_text()) if FILE.exists() else {}


def _save(users):
    FILE.write_text(json.dumps(users, indent=2))


def _hash(password, salt):
    return hashlib.sha256((salt + password).encode()).hexdigest()


def register(username, password, subjects):
    username = username.strip().lower()
    if not username or len(password) < 4:
        return False, "Enter a username and a password of at least 4 characters."
    if not subjects:
        return False, "Select at least one subject."
    users = _load()
    if username in users:
        return False, "That username already exists. Please log in."
    salt = os.urandom(8).hex()
    users[username] = {"salt": salt, "hash": _hash(password, salt), "subjects": subjects,
                       "answers": [], "snapshots": [], "usage": []}
    _save(users)
    return True, "Account created. You can log in now."


def login(username, password):
    username = username.strip().lower()
    u = _load().get(username)
    if not u or u["hash"] != _hash(password, u["salt"]):
        return None
    return {"username": username, "subjects": u["subjects"], "answers": u["answers"],
            "snapshots": u["snapshots"], "usage": u["usage"]}


def save_progress(username, subjects, answers, snapshots, usage):
    users = _load()
    if username in users:
        users[username].update({"subjects": subjects, "answers": answers,
                                "snapshots": snapshots, "usage": usage})
        _save(users)


def handle_event(res, state):
    """Process one event from the login page. Returns 'ok' (logged in), 'new' (rerun needed) or None."""
    if not res or res.get("id") == state.get("l_last"):
        return None
    state["l_last"] = res.get("id")
    state["l_err"], state["l_flash"] = "", ""
    state["l_nonce"] = state.get("l_nonce", 0) + 1
    user, pw = res.get("username", ""), res.get("password", "")
    if res.get("action") == "register":
        ok, msg = register(user, pw, res.get("subjects") or [])
        state["l_flash" if ok else "l_err"] = "Account created. Please log in." if ok else msg
        return "new"
    d = login(user, pw)
    if d:
        state["login_data"] = d
        return "ok"
    state["l_err"] = "Wrong username or password."
    return "new"