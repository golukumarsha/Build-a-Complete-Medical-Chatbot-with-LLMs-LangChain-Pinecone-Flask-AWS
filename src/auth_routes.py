# src/auth_routes.py — JWT Authentication Routes
"""
Blueprint for all auth endpoints:
  POST /auth/register   — naya account banao
  POST /auth/login      — login karo, JWT milega
  POST /auth/logout     — client side token delete
  GET  /auth/me         — apna profile dekho
  GET  /auth/history    — apni chat history dekho
  DELETE /auth/history  — apni chat history delete karo
  PUT  /auth/doctor-info — doctor apni info update kare
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, jwt_required,
    get_jwt_identity, get_jwt
)
from src.auth_models import (
    create_user, verify_user, get_user_by_id,
    get_user_chat_history, delete_user_chat_history,
    update_doctor_info, get_all_users_for_admin
)
import re

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


# ── Helpers ───────────────────────────────────────────────────
def _validate_email(email: str) -> bool:
    return bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$", email))


def _validate_password(pw: str) -> str | None:
    """Returns error string ya None agar sahi hai."""
    if len(pw) < 6:
        return "Password kam se kam 6 characters ka hona chahiye"
    return None


# ═══════════════════════════════════════════════════════════════
#  REGISTER
# ═══════════════════════════════════════════════════════════════
@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Body (JSON):
      { "username": "...", "email": "...", "password": "...", "role": "patient|doctor" }
    """
    data = request.get_json(silent=True) or {}

    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip()
    password = (data.get("password") or "").strip()
    role = (data.get("role") or "patient").strip().lower()

    # ── Validation ────────────────────────────────────────────
    if not username or not email or not password:
        return jsonify({"success": False,
                        "error": "Username, email aur password zaroori hain"}), 400

    if len(username) < 3:
        return jsonify({"success": False,
                        "error": "Username kam se kam 3 characters ka hona chahiye"}), 400

    if not _validate_email(email):
        return jsonify({"success": False, "error": "Valid email daalo"}), 400

    pw_err = _validate_password(password)
    if pw_err:
        return jsonify({"success": False, "error": pw_err}), 400

    if role not in ("patient", "doctor"):
        return jsonify({"success": False,
                        "error": "Role sirf 'patient' ya 'doctor' ho sakta hai"}), 400

    # ── Create user ───────────────────────────────────────────
    result = create_user(username, email, password, role)
    if not result["success"]:
        return jsonify(result), 409

    # Auto-login after register — token do
    token = create_access_token(
        identity=result["user_id"],
        additional_claims={"role": role, "username": username}
    )

    return jsonify({
        "success": True,
        "message": f"🎉 Welcome {username}! Account ban gaya.",
        "token":   token,
        "user": {
            "user_id":  result["user_id"],
            "username": username,
            "email":    email,
            "role":     role
        }
    }), 201


# ═══════════════════════════════════════════════════════════════
#  LOGIN
# ═══════════════════════════════════════════════════════════════
@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Body (JSON): { "email": "...", "password": "..." }
    """
    data = request.get_json(silent=True) or {}

    email = (data.get("email") or "").strip()
    password = (data.get("password") or "").strip()

    if not email or not password:
        return jsonify({"success": False,
                        "error": "Email aur password daalo"}), 400

    result = verify_user(email, password)
    if not result["success"]:
        return jsonify(result), 401

    user = result["user"]
    token = create_access_token(
        identity=user["user_id"],
        additional_claims={
            "role":     user["role"],
            "username": user["username"]
        }
    )

    return jsonify({
        "success": True,
        "message": f"✅ Welcome back, {user['username']}!",
        "token":   token,
        "user":    user
    })


# ═══════════════════════════════════════════════════════════════
#  ME (profile)
# ═══════════════════════════════════════════════════════════════
@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"success": False, "error": "User nahi mila"}), 404
    return jsonify({"success": True, "user": user})


# ═══════════════════════════════════════════════════════════════
#  CHAT HISTORY
# ═══════════════════════════════════════════════════════════════
@auth_bp.route("/history", methods=["GET"])
@jwt_required()
def my_history():
    user_id = get_jwt_identity()
    limit = int(request.args.get("limit", 50))
    chats = get_user_chat_history(user_id, limit=limit)
    return jsonify({"success": True, "count": len(chats), "data": chats})


@auth_bp.route("/history", methods=["DELETE"])
@jwt_required()
def clear_my_history():
    user_id = get_jwt_identity()
    result = delete_user_chat_history(user_id)
    return jsonify({
        "success": True,
        "message": f"🗑️ {result['deleted']} messages delete ho gaye!"
    })


# ═══════════════════════════════════════════════════════════════
#  DOCTOR INFO UPDATE
# ═══════════════════════════════════════════════════════════════
@auth_bp.route("/doctor-info", methods=["PUT"])
@jwt_required()
def update_doc_info():
    claims = get_jwt()
    if claims.get("role") != "doctor":
        return jsonify({"success": False,
                        "error": "Sirf doctors hi yeh update kar sakte hain"}), 403

    data = request.get_json(silent=True) or {}
    user_id = get_jwt_identity()
    specialization = data.get("specialization", "")
    license_no = data.get("license_no",     "")
    hospital = data.get("hospital",       "")

    result = update_doctor_info(user_id, specialization, license_no, hospital)
    return jsonify(result)


# ═══════════════════════════════════════════════════════════════
#  LOGOUT (client side — token blacklist optional)
# ═══════════════════════════════════════════════════════════════
@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    """
    JWT stateless hota hai — client apna token delete kar de.
    Server side message return karo.
    """
    claims = get_jwt()
    return jsonify({
        "success": True,
        "message": f"👋 Alag ho gaya, {claims.get('username', '')}!"
    })


# ═══════════════════════════════════════════════════════════════
#  ADMIN — sabse users dekho (role=doctor only)
# ═══════════════════════════════════════════════════════════════
@auth_bp.route("/admin/users", methods=["GET"])
@jwt_required()
def admin_users():
    claims = get_jwt()
    if claims.get("role") != "doctor":
        return jsonify({"success": False, "error": "Access denied — Doctors only"}), 403
    users = get_all_users_for_admin()
    return jsonify({"success": True, "count": len(users), "data": users})
