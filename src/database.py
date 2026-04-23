"""
src/database.py
MongoDB — 2 Collections:
  1. medicines     — medicine/disease info
  2. search_logs   — user ne chatbot mein kya kya search kiya
"""

from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT
from pymongo.errors import DuplicateKeyError
from datetime import datetime, timezone, timedelta
import os


# ═══════════════════════════════════════════════════════════
#  CONNECTION
# ═══════════════════════════════════════════════════════════

def get_db():
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
    client = MongoClient(MONGO_URI)
    return client["medibot_db"]


def get_medicines_collection():
    col = get_db()["medicines"]
    col.create_index([("name", ASCENDING)], unique=True)
    col.create_index([("name", TEXT), ("category", TEXT), ("symptoms", TEXT)])
    return col


def get_search_logs_collection():
    col = get_db()["search_logs"]
    col.create_index([("searched_at", DESCENDING)])
    col.create_index([("query", TEXT)])
    return col


# ═══════════════════════════════════════════════════════════
#  SEARCH LOGS
# ═══════════════════════════════════════════════════════════

def save_search_log(query: str, ai_response: str,
                    matched_medicine: str = None,
                    image_found: bool = False,
                    language: str = "english"):
    """
    Har chatbot query MongoDB mein save karo.
    Fields: query, ai_response, matched_medicine, image_found, language, searched_at
    """
    col = get_search_logs_collection()
    log = {
        "query":            query.strip(),
        "ai_response":      ai_response.strip(),
        "matched_medicine": matched_medicine,
        "image_found":      image_found,
        "language":         language,           # ← NEW: hindi / hinglish / english
        "searched_at":      datetime.now(timezone.utc),
    }
    try:
        col.insert_one(log)
        print(f"[DB] Search log saved: '{query[:40]}' [{language}]")
    except Exception as e:
        print(f"[Search Log Error] {e}")


def get_search_logs(limit: int = 50) -> list:
    """Recent search logs — latest pehle"""
    col = get_search_logs_collection()
    logs = col.find({}, {"_id": 0}).sort(
        "searched_at", DESCENDING).limit(limit)
    result = []
    for log in logs:
        if "searched_at" in log:
            # IST = UTC+5:30
            ist_time = log["searched_at"] + timedelta(hours=5, minutes=30)
            log["searched_at"] = ist_time.strftime("%d %b %Y, %I:%M %p")
        result.append(log)
    return result


def get_search_stats() -> dict:
    """
    Analytics:
      - total_searches
      - today_searches  ← FIX: pehle missing tha
      - image_found
      - medicine_matched
      - top_queries
      - language_breakdown
    """
    col = get_search_logs_collection()
    total = col.count_documents({})

    # Aaj ki searches (IST midnight se)
    now_utc = datetime.now(timezone.utc)
    ist_today = (now_utc + timedelta(hours=5, minutes=30)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    utc_today = ist_today - timedelta(hours=5, minutes=30)
    today_count = col.count_documents({"searched_at": {"$gte": utc_today}})

    # Top 10 queries
    pipeline = [
        {"$group": {"_id": "$query", "count": {"$sum": 1}}},
        {"$sort": {"count": DESCENDING}},
        {"$limit": 10}
    ]
    top_queries = [
        {"query": r["_id"], "count": r["count"]}
        for r in col.aggregate(pipeline)
    ]

    # Image & medicine stats
    image_found_count = col.count_documents({"image_found": True})
    medicine_match_count = col.count_documents(
        {"matched_medicine": {"$ne": None, "$exists": True}}
    )

    # Language breakdown
    lang_pipeline = [
        {"$group": {"_id": "$language", "count": {"$sum": 1}}}
    ]
    lang_breakdown = {
        r["_id"]: r["count"]
        for r in col.aggregate(lang_pipeline)
        if r["_id"]
    }

    return {
        "total_searches":   total,
        "today_searches":   today_count,       # ← FIX
        "image_found":      image_found_count,
        "medicine_matched": medicine_match_count,
        "top_queries":      top_queries,
        "language_stats":   lang_breakdown,
    }


def delete_all_logs() -> dict:
    col = get_search_logs_collection()
    result = col.delete_many({})
    return {"deleted": result.deleted_count}


# ═══════════════════════════════════════════════════════════
#  MEDICINES — CRUD
# ═══════════════════════════════════════════════════════════

def insert_medicine(data: dict) -> dict:
    col = get_medicines_collection()
    data["created_at"] = datetime.now(timezone.utc)
    data["updated_at"] = datetime.now(timezone.utc)
    data["name"] = data["name"].strip().title()
    try:
        result = col.insert_one(data)
        return {"success": True, "message": f"'{data['name']}' add hua!", "id": str(result.inserted_id)}
    except DuplicateKeyError:
        return {"success": False, "message": f"'{data['name']}' pehle se hai!"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def insert_many_medicines(data_list: list) -> dict:
    results = {"success": 0, "failed": 0, "errors": []}
    for item in data_list:
        r = insert_medicine(item)
        if r["success"]:
            results["success"] += 1
        else:
            results["failed"] += 1
            results["errors"].append(r["message"])
    return results


def get_all_medicines() -> list:
    col = get_medicines_collection()
    return list(col.find({}, {"_id": 0}).sort("name", ASCENDING))


def get_by_category(category: str) -> list:
    col = get_medicines_collection()
    return list(col.find({"category": category}, {"_id": 0}).sort("name", ASCENDING))


def search_medicine(query: str) -> list:
    col = get_medicines_collection()
    results = list(col.find(
        {"$text": {"$search": query}},
        {"_id": 0, "score": {"$meta": "textScore"}}
    ).sort([("score", {"$meta": "textScore"})]).limit(10))

    if not results:
        import re
        pattern = re.compile(query, re.IGNORECASE)
        results = list(col.find(
            {"$or": [
                {"name": pattern}, {"symptoms": pattern},
                {"category": pattern}, {"description": pattern}
            ]}, {"_id": 0}
        ).limit(10))
    return results


def get_medicine_by_name(name: str):
    col = get_medicines_collection()
    return col.find_one({"name": name.strip().title()}, {"_id": 0})


def update_medicine(name: str, update_data: dict) -> dict:
    col = get_medicines_collection()
    update_data["updated_at"] = datetime.now(timezone.utc)
    result = col.update_one(
        {"name": name.strip().title()},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        return {"success": False, "message": f"'{name}' nahi mila"}
    return {"success": True, "message": f"'{name}' update hua!"}


def delete_medicine(name: str) -> dict:
    col = get_medicines_collection()
    result = col.delete_one({"name": name.strip().title()})
    if result.deleted_count == 0:
        return {"success": False, "message": f"'{name}' nahi mila"}
    return {"success": True, "message": f"'{name}' delete ho gaya!"}


def get_stats() -> dict:
    col = get_medicines_collection()
    return {
        "total":       col.count_documents({}),
        "diseases":    col.count_documents({"category": "Disease"}),
        "medicines":   col.count_documents({"category": "Medicine"}),
        "supplements": col.count_documents({"category": "Supplement"}),
    }
