"""
backend/auth.py
Simple file-based authentication (JSON storage).
"""

import os, json, hashlib, secrets
from datetime import datetime

USERS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "users.json")


def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode()).hexdigest()


def _load_users() -> dict:
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)


def _save_users(users: dict):
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def register_user(username: str, password: str, full_name: str = "", email: str = "") -> dict:
    username = username.strip().lower()
    if len(username) < 3:
        return {"success": False, "error": "Username minimal 3 karakter."}
    if len(password) < 6:
        return {"success": False, "error": "Password minimal 6 karakter."}

    users = _load_users()
    if username in users:
        return {"success": False, "error": "Username sudah digunakan."}

    salt = secrets.token_hex(16)
    users[username] = {
        "username":   username,
        "full_name":  full_name.strip(),
        "email":      email.strip(),
        "salt":       salt,
        "password":   _hash_password(password, salt),
        "created_at": datetime.now().strftime("%d %b %Y %H:%M"),
        "upload_count": 0,
        "last_login": "",
        "avatar_url": "",
    }
    _save_users(users)
    return {"success": True}


def login_user(username: str, password: str) -> dict:
    username = username.strip().lower()
    users = _load_users()
    if username not in users:
        return {"success": False, "error": "Username atau password salah."}

    u = users[username]
    if _hash_password(password, u["salt"]) != u["password"]:
        return {"success": False, "error": "Username atau password salah."}

    # update last login
    u["last_login"] = datetime.now().strftime("%d %b %Y %H:%M")
    _save_users(users)

    profile = {k: v for k, v in u.items() if k not in ("salt", "password")}
    return {"success": True, "user": profile}


def get_user(username: str) -> dict | None:
    users = _load_users()
    u = users.get(username.lower())
    if not u:
        return None
    return {k: v for k, v in u.items() if k not in ("salt", "password")}


def update_user(username: str, full_name: str = None, email: str = None,
                new_password: str = None, current_password: str = None,
                avatar_url: str = None) -> dict:
    users = _load_users()
    username = username.lower()
    if username not in users:
        return {"success": False, "error": "User tidak ditemukan."}

    u = users[username]

    # Ubah password (butuh verifikasi password lama)
    if new_password:
        if not current_password:
            return {"success": False, "error": "Password saat ini diperlukan untuk mengubah password."}
        if _hash_password(current_password, u["salt"]) != u["password"]:
            return {"success": False, "error": "Password saat ini salah."}
        if len(new_password) < 6:
            return {"success": False, "error": "Password baru minimal 6 karakter."}
        new_salt = secrets.token_hex(16)
        u["salt"]     = new_salt
        u["password"] = _hash_password(new_password, new_salt)

    # Update nama & email
    if full_name is not None:
        u["full_name"] = full_name.strip()
    if email is not None:
        u["email"] = email.strip()
    if avatar_url is not None:
        u["avatar_url"] = avatar_url

    _save_users(users)
    profile = {k: v for k, v in u.items() if k not in ("salt", "password")}
    return {"success": True, "user": profile}


def update_profile_info(username: str, full_name: str, email: str) -> dict:
    """Update hanya nama dan email tanpa menyentuh password."""
    users = _load_users()
    username = username.lower()
    if username not in users:
        return {"success": False, "error": "User tidak ditemukan."}
    u = users[username]
    u["full_name"] = full_name.strip()
    u["email"]     = email.strip()
    _save_users(users)
    profile = {k: v for k, v in u.items() if k not in ("salt", "password")}
    return {"success": True, "user": profile}


def update_password(username: str, current_password: str, new_password: str) -> dict:
    """Update password dengan verifikasi password lama."""
    users = _load_users()
    username = username.lower()
    if username not in users:
        return {"success": False, "error": "User tidak ditemukan."}
    u = users[username]
    if not current_password:
        return {"success": False, "error": "Password saat ini diperlukan."}
    if _hash_password(current_password, u["salt"]) != u["password"]:
        return {"success": False, "error": "Password saat ini salah."}
    if len(new_password) < 6:
        return {"success": False, "error": "Password baru minimal 6 karakter."}
    new_salt      = secrets.token_hex(16)
    u["salt"]     = new_salt
    u["password"] = _hash_password(new_password, new_salt)
    _save_users(users)
    profile = {k: v for k, v in u.items() if k not in ("salt", "password")}
    return {"success": True, "user": profile}


def increment_upload(username: str):
    users = _load_users()
    if username in users:
        users[username]["upload_count"] = users[username].get("upload_count", 0) + 1
        _save_users(users)
