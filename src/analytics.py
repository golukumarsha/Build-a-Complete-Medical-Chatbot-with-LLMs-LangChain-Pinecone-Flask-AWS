# src/analytics.py — Analytics Dashboard Backend for MediBot
"""
MongoDB aggregation pipelines use karta hai:
- Most searched queries
- Daily/Weekly trends
- Disease vs Medicine ratio
- Peak hours analysis
- User activity stats
"""

import os
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient, DESCENDING

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
    db = client["medibot_db"]
    logs_col = db["search_logs"]       # existing collection
    sessions_col = db["conversation_sessions"]  # memory collection
    users_col = db["users"]             # auth collection
    ANALYTICS_OK = True
except Exception as e:
    ANALYTICS_OK = False
    print(f"[Analytics] MongoDB error: {e}")


# ══════════════════════════════════════════════════════════════
#  1. OVERVIEW STATS — top numbers
# ══════════════════════════════════════════════════════════════
def get_overview_stats() -> dict:
    """Total searches, users, today's searches etc."""
    try:
        now = datetime.now(timezone.utc)
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week = today - timedelta(days=7)

        total_searches = logs_col.count_documents({})
        today_searches = logs_col.count_documents(
            {"timestamp": {"$gte": today}})
        week_searches = logs_col.count_documents({"timestamp": {"$gte": week}})

        # Image found count
        image_found = logs_col.count_documents({"image_found": True})

        # Total users (agar auth hai)
        try:
            total_users = users_col.count_documents({})
            doctor_count = users_col.count_documents({"role": "doctor"})
            patient_count = users_col.count_documents({"role": "patient"})
        except Exception:
            total_users = doctor_count = patient_count = 0

        # Active sessions
        try:
            active_sessions = sessions_col.count_documents(
                {"updated_at": {"$gte": today}}
            )
        except Exception:
            active_sessions = 0

        return {
            "total_searches":  total_searches,
            "today_searches":  today_searches,
            "week_searches":   week_searches,
            "image_found":     image_found,
            "total_users":     total_users,
            "doctor_count":    doctor_count,
            "patient_count":   patient_count,
            "active_sessions": active_sessions,
        }
    except Exception as e:
        print(f"[Analytics] overview error: {e}")
        return {}


# ══════════════════════════════════════════════════════════════
#  2. MOST SEARCHED — top queries
# ══════════════════════════════════════════════════════════════
def get_top_queries(limit: int = 10) -> list:
    """Sabse zyada search hone wali queries."""
    try:
        pipeline = [
            {"$group": {
                "_id":   {"$toLower": "$query"},
                "count": {"$sum": 1},
                "last":  {"$max": "$timestamp"}
            }},
            {"$sort":  {"count": -1}},
            {"$limit": limit},
            {"$project": {"query": "$_id", "count": 1, "last": 1, "_id": 0}}
        ]
        return list(logs_col.aggregate(pipeline))
    except Exception as e:
        print(f"[Analytics] top_queries error: {e}")
        return []


# ══════════════════════════════════════════════════════════════
#  3. TOP MATCHED MEDICINES
# ══════════════════════════════════════════════════════════════
def get_top_medicines(limit: int = 8) -> list:
    """Sabse zyada match hone wali medicines."""
    try:
        pipeline = [
            {"$match":  {"matched_medicine": {"$ne": None}}},
            {"$group":  {
                "_id":   "$matched_medicine",
                "count": {"$sum": 1}
            }},
            {"$sort":   {"count": -1}},
            {"$limit":  limit},
            {"$project": {"medicine": "$_id", "count": 1, "_id": 0}}
        ]
        return list(logs_col.aggregate(pipeline))
    except Exception as e:
        print(f"[Analytics] top_medicines error: {e}")
        return []


# ══════════════════════════════════════════════════════════════
#  4. DAILY TREND — last 14 days
# ══════════════════════════════════════════════════════════════
def get_daily_trend(days: int = 14) -> list:
    """Last N days ka daily search count."""
    try:
        start = datetime.now(timezone.utc) - timedelta(days=days)
        pipeline = [
            {"$match":  {"timestamp": {"$gte": start}}},
            {"$group":  {
                "_id": {
                    "year":  {"$year":       "$timestamp"},
                    "month": {"$month":      "$timestamp"},
                    "day":   {"$dayOfMonth": "$timestamp"},
                },
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id.year": 1, "_id.month": 1, "_id.day": 1}},
            {"$project": {
                "_id":   0,
                "date":  {
                    "$dateToString": {
                        "format": "%d %b",
                        "date": {
                            "$dateFromParts": {
                                "year":  "$_id.year",
                                "month": "$_id.month",
                                "day":   "$_id.day"
                            }
                        }
                    }
                },
                "count": 1
            }}
        ]
        results = list(logs_col.aggregate(pipeline))

        # Missing days ko 0 se fill karo
        all_days = {}
        for i in range(days):
            d = datetime.now(timezone.utc) - timedelta(days=days - 1 - i)
            key = d.strftime("%d %b")
            all_days[key] = 0
        for r in results:
            all_days[r["date"]] = r["count"]

        return [{"date": k, "count": v} for k, v in all_days.items()]
    except Exception as e:
        print(f"[Analytics] daily_trend error: {e}")
        return []


# ══════════════════════════════════════════════════════════════
#  5. HOURLY PATTERN — peak hours
# ══════════════════════════════════════════════════════════════
def get_hourly_pattern() -> list:
    """Din ke kis time sabse zyada queries aati hain."""
    try:
        pipeline = [
            {"$group": {
                "_id":   {"$hour": "$timestamp"},
                "count": {"$sum": 1}
            }},
            {"$sort":  {"_id": 1}},
            {"$project": {
                "_id":  0,
                "hour": "$_id",
                "count": 1,
                "label": {
                    "$concat": [
                        {"$toString": "$_id"}, ":00"
                    ]
                }
            }}
        ]
        results = {r["hour"]: r["count"] for r in logs_col.aggregate(pipeline)}

        # All 24 hours fill karo
        return [
            {"hour": h, "label": f"{h:02d}:00", "count": results.get(h, 0)}
            for h in range(24)
        ]
    except Exception as e:
        print(f"[Analytics] hourly error: {e}")
        return []


# ══════════════════════════════════════════════════════════════
#  6. WEEKLY COMPARISON
# ══════════════════════════════════════════════════════════════
def get_weekly_comparison() -> list:
    """Is hafte vs pichle hafte comparison."""
    try:
        now = datetime.now(timezone.utc)
        this_week = now - timedelta(days=7)
        last_week = now - timedelta(days=14)

        days_data = []
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        for i in range(7):
            # This week
            tw_start = (this_week + timedelta(days=i)
                        ).replace(hour=0,  minute=0, second=0, microsecond=0)
            tw_end = (this_week + timedelta(days=i)
                      ).replace(hour=23, minute=59, second=59)

            # Last week
            lw_start = (last_week + timedelta(days=i)
                        ).replace(hour=0,  minute=0, second=0, microsecond=0)
            lw_end = (last_week + timedelta(days=i)
                      ).replace(hour=23, minute=59, second=59)

            tw_count = logs_col.count_documents(
                {"timestamp": {"$gte": tw_start, "$lte": tw_end}})
            lw_count = logs_col.count_documents(
                {"timestamp": {"$gte": lw_start, "$lte": lw_end}})

            days_data.append({
                "day":       day_names[i],
                "this_week": tw_count,
                "last_week": lw_count,
            })

        return days_data
    except Exception as e:
        print(f"[Analytics] weekly error: {e}")
        return []


# ══════════════════════════════════════════════════════════════
#  7. IMAGE STATS
# ══════════════════════════════════════════════════════════════
def get_image_stats() -> dict:
    """Kitni queries mein image mili / nahi mili."""
    try:
        total = logs_col.count_documents({})
        with_img = logs_col.count_documents({"image_found": True})
        without = total - with_img
        return {
            "with_image":    with_img,
            "without_image": without,
            "total":         total,
            "pct":           round((with_img / total * 100) if total else 0, 1)
        }
    except Exception as e:
        return {"with_image": 0, "without_image": 0, "total": 0, "pct": 0}


# ══════════════════════════════════════════════════════════════
#  8. RECENT ACTIVITY — last 20 searches
# ══════════════════════════════════════════════════════════════
def get_recent_activity(limit: int = 20) -> list:
    """Recent searches ki list."""
    try:
        docs = logs_col.find(
            {},
            {"query": 1, "matched_medicine": 1,
                "image_found": 1, "timestamp": 1, "_id": 0},
            sort=[("timestamp", DESCENDING)],
            limit=limit
        )
        results = []
        for d in docs:
            results.append({
                "query":    d.get("query",            ""),
                "medicine": d.get("matched_medicine", "—"),
                "image":    d.get("image_found",      False),
                "time":     d["timestamp"].strftime("%d %b, %I:%M %p")
                if d.get("timestamp") else "—"
            })
        return results
    except Exception as e:
        return []


# ══════════════════════════════════════════════════════════════
#  9. COMBINED — ek hi call mein sab data
# ══════════════════════════════════════════════════════════════
def get_all_analytics() -> dict:
    """Dashboard ke liye ek hi API call mein sab data."""
    return {
        "overview":        get_overview_stats(),
        "top_queries":     get_top_queries(10),
        "top_medicines":   get_top_medicines(8),
        "daily_trend":     get_daily_trend(14),
        "hourly_pattern":  get_hourly_pattern(),
        "weekly_compare":  get_weekly_comparison(),
        "image_stats":     get_image_stats(),
        "recent_activity": get_recent_activity(20),
    }
