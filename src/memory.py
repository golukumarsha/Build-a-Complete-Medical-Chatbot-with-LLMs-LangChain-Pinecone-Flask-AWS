# src/memory.py — Conversation Memory for MediBot
"""
Har session ki conversation MongoDB mein save hoti hai.
Session = ek browser tab ki poori conversation.

Collection: conversation_sessions
  _id        : session_id (string — browser se aata hai)
  messages   : [ {role: "human"/"ai", content: "..."}, ... ]
  created_at : datetime
  updated_at : datetime
  user_id    : optional (agar logged in hai)
"""

import os
from datetime import datetime, timezone
from pymongo import MongoClient, DESCENDING

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
    db = client["medibot_db"]
    sessions = db["conversation_sessions"]
    sessions.create_index([("updated_at", DESCENDING)])
    sessions.create_index([("user_id",    DESCENDING)])
    MEMORY_OK = True
except Exception as e:
    MEMORY_OK = False
    print(f"[Memory] MongoDB nahi mila: {e}")


# ── Get history from MongoDB ──────────────────────────────────
def get_session_history(session_id: str) -> list:
    """
    Session ki poori message history lao.
    Returns: [ {"role": "human", "content": "..."}, ... ]
    """
    if not MEMORY_OK:
        return []
    try:
        doc = sessions.find_one({"_id": session_id})
        return doc["messages"] if doc else []
    except Exception as e:
        print(f"[Memory] get_session_history error: {e}")
        return []


# ── Save new message pair ─────────────────────────────────────
def save_message_pair(session_id: str, human_msg: str,
                      ai_msg: str, user_id: str = None):
    """
    User ka message + AI ka jawab dono MongoDB mein save karo.
    Last 10 pairs hi rakho — purana delete ho jata hai.
    """
    if not MEMORY_OK:
        return

    try:
        now = datetime.now(timezone.utc)
        doc = sessions.find_one({"_id": session_id})

        if doc:
            messages = doc.get("messages", [])
        else:
            messages = []

        # Naya pair add karo
        messages.append({"role": "human", "content": human_msg})
        messages.append({"role": "ai",    "content": ai_msg})

        # Sirf last 20 messages rakho (10 pairs) — context window chhota rakho
        if len(messages) > 20:
            messages = messages[-20:]

        sessions.update_one(
            {"_id": session_id},
            {"$set": {
                "messages":   messages,
                "updated_at": now,
                "user_id":    user_id,
            },
                "$setOnInsert": {"created_at": now}},
            upsert=True
        )
    except Exception as e:
        print(f"[Memory] save_message_pair error: {e}")


# ── Delete session ────────────────────────────────────────────
def delete_session(session_id: str):
    """Session ki saari history delete karo."""
    if not MEMORY_OK:
        return
    try:
        sessions.delete_one({"_id": session_id})
    except Exception as e:
        print(f"[Memory] delete_session error: {e}")


# ── Build history string for prompt ──────────────────────────
def build_history_text(messages: list) -> str:
    """
    Message list ko readable string mein convert karo
    jo system prompt mein inject hoga.
    """
    if not messages:
        return "Koi purani conversation nahi hai."

    lines = []
    for m in messages:
        role = "User" if m["role"] == "human" else "MediBot"
        content = m["content"]
        # Long responses trim karo
        if len(content) > 300:
            content = content[:300] + "..."
        lines.append(f"{role}: {content}")

    return "\n".join(lines)
