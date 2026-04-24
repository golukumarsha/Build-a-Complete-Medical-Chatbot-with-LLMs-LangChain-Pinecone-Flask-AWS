# src/auth_models.py — User Authentication Models for MediBot
"""
MongoDB mein user data store karne ke liye functions.
Collections:
  - users        : registered users (doctors + patients)
  - chat_history : har user ka personal chat history
"""

import os
from datetime import datetime, timezone
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError
import bcrypt

# ── MongoDB Connection ────────────────────────────────────────
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client["medibot_db"]

users_col = db["users"]
history_col = db["chat_history"]

# ── Indexes (first time mein ek baar chalega) ─────────────────
users_col.create_index([("email", ASCENDING)],    unique=True)
users_col.create_index([("username", ASCENDING)], unique=True)
history_col.create_index([("user_id", ASCENDING)])
history_col.create_index([("created_at", DESCENDING)])


# ═══════════════════════════════════════════════════════════════
#  USER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def create_user(username: str, email: str, password: str, role: str = "patient") -> dict:
    """
    Naya user register karo.
    role: 'patient' ya 'doctor'
    Returns: {"success": True, "user_id": "..."} ya {"success": False, "error": "..."}
    """
    if role not in ("patient", "doctor"):
        return {"success": False, "error": "Role sirf 'patient' ya 'doctor' ho sakta hai"}

    # Password hash karo
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    user_doc = {
        "username":   username.strip().lower(),
        "email":      email.strip().lower(),
        "password":   hashed,
        "role":       role,
        "created_at": datetime.now(timezone.utc),
        "last_login": None,
        "is_active":  True,
        # Doctor ke liye extra fields
        "doctor_info": {
            "specialization": "",
            "license_no":     "",
            "hospital":       ""
        } if role == "doctor" else None
    }

    try:
        result = users_col.insert_one(user_doc)
        return {"success": True, "user_id": str(result.inserted_id)}
    except DuplicateKeyError as e:
        err_str = str(e)
        if "email" in err_str:
            return {"success": False, "error": "Yeh email already registered hai"}
        if "username" in err_str:
            return {"success": False, "error": "Yeh username already liya ja chuka hai"}
        return {"success": False, "error": "Duplicate entry"}


def verify_user(email: str, password: str) -> dict:
    """
    Login verify karo.
    Returns: {"success": True, "user": {...}} ya {"success": False, "error": "..."}
    """
    user = users_col.find_one({"email": email.strip().lower()})
    if not user:
        return {"success": False, "error": "Email registered nahi hai"}

    if not user.get("is_active", True):
        return {"success": False, "error": "Account deactivated hai"}

    if not bcrypt.checkpw(password.encode("utf-8"), user["password"]):
        return {"success": False, "error": "Password galat hai"}

    # Last login update karo
    users_col.update_one(
        {"_id": user["_id"]},
        {"$set": {"last_login": datetime.now(timezone.utc)}}
    )

    return {
        "success": True,
        "user": _format_user(user)
    }


def get_user_by_id(user_id: str) -> dict | None:
    """User ID se user fetch karo."""
    from bson import ObjectId
    try:
        user = users_col.find_one({"_id": ObjectId(user_id)})
        return _format_user(user) if user else None
    except Exception:
        return None


def get_user_by_email(email: str) -> dict | None:
    user = users_col.find_one({"email": email.strip().lower()})
    return _format_user(user) if user else None


def update_doctor_info(user_id: str, specialization: str, license_no: str, hospital: str) -> dict:
    """Doctor apni professional info update kar sake."""
    from bson import ObjectId
    try:
        users_col.update_one(
            {"_id": ObjectId(user_id), "role": "doctor"},
            {"$set": {
                "doctor_info.specialization": specialization,
                "doctor_info.license_no":     license_no,
                "doctor_info.hospital":       hospital
            }}
        )
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _format_user(user: dict) -> dict:
    """MongoDB doc ko JSON-safe dict mein convert karo (password remove)."""
    return {
        "user_id":    str(user["_id"]),
        "username":   user["username"],
        "email":      user["email"],
        "role":       user["role"],
        "created_at": user["created_at"].isoformat() if user.get("created_at") else None,
        "last_login": user["last_login"].isoformat() if user.get("last_login") else None,
        "doctor_info": user.get("doctor_info"),
        "is_active":  user.get("is_active", True)
    }


# ═══════════════════════════════════════════════════════════════
#  CHAT HISTORY FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def save_chat_message(user_id: str, role: str, message: str,
                      ai_response: str = None, image_data: dict = None) -> dict:
    """
    Chat message save karo user ke liye.
    role: 'patient' ya 'doctor' — kis role mein chat tha
    """
    doc = {
        "user_id":    user_id,
        "user_role":  role,
        "message":    message,
        "response":   ai_response,
        "image":      image_data,
        "created_at": datetime.now(timezone.utc)
    }
    result = history_col.insert_one(doc)
    return {"success": True, "chat_id": str(result.inserted_id)}


def get_user_chat_history(user_id: str, limit: int = 50) -> list:
    """Ek user ki saari chat history lao (latest pehle)."""
    chats = history_col.find(
        {"user_id": user_id},
        sort=[("created_at", DESCENDING)],
        limit=limit
    )
    result = []
    for c in chats:
        result.append({
            "chat_id":    str(c["_id"]),
            "message":    c.get("message", ""),
            "response":   c.get("response", ""),
            "image":      c.get("image"),
            "created_at": c["created_at"].isoformat() if c.get("created_at") else None
        })
    return result


def delete_user_chat_history(user_id: str) -> dict:
    """User apni saari chat history delete kar sake."""
    result = history_col.delete_many({"user_id": user_id})
    return {"success": True, "deleted": result.deleted_count}


def get_all_users_for_admin() -> list:
    """Admin ke liye saare users ki list (passwords nahi)."""
    users = users_col.find({}, sort=[("created_at", DESCENDING)])
    return [_format_user(u) for u in users]
