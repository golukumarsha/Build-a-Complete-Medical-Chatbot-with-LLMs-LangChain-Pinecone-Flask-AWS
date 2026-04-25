# src/whatsapp_bot.py — MediBot WhatsApp Integration via Twilio
"""
Twilio WhatsApp Sandbox use karta hai.

Flow:
  User WhatsApp pe message karta hai
  → Twilio webhook app.py /webhook/whatsapp pe POST bhejta hai
  → Yahan RAG chain se answer milta hai
  → TwiML response bhejte hain → User ko WhatsApp pe reply aata hai

Commands supported:
  /help           → Available commands
  /symptoms <...> → Symptom checker
  /drug <A> vs <B>→ Drug interaction check
  /reset          → Conversation history clear

Setup:
  1. Twilio account banao: https://twilio.com
  2. WhatsApp Sandbox activate karo (Messaging → Try it out → WhatsApp)
  3. Sandbox number save karo: whatsapp:+14155238886
  4. Webhook URL set karo: https://your-domain/webhook/whatsapp
"""

import os
import re
from datetime import datetime

# ── Twilio ────────────────────────────────────────────────────
try:
    from twilio.twiml.messaging_response import MessagingResponse
    from twilio.request_validator import RequestValidator
    TWILIO_OK = True
except ImportError:
    TWILIO_OK = False
    print("[WhatsApp] twilio install nahi hai: pip install twilio")

# ── Session store (in-memory, production mein Redis use karo) ──
# { "whatsapp:+91XXXXXXXXXX": { "history": [...], "last_seen": datetime } }
_wa_sessions: dict = {}

MAX_HISTORY = 6    # kitne purane messages yaad rakhe
SESSION_TTL_H = 6    # session 6 ghante ke baad expire


# ══════════════════════════════════════════════════════════════
#  SESSION HELPERS
# ══════════════════════════════════════════════════════════════

def _get_session(phone: str) -> list:
    """User ka conversation history lo. Expire ho gaya to fresh start."""
    now = datetime.now()
    sess = _wa_sessions.get(phone)
    if sess:
        hours_ago = (now - sess["last_seen"]).total_seconds() / 3600
        if hours_ago < SESSION_TTL_H:
            sess["last_seen"] = now
            return sess["history"]
    # Fresh session
    _wa_sessions[phone] = {"history": [], "last_seen": now}
    return _wa_sessions[phone]["history"]


def _save_to_session(phone: str, user_msg: str, bot_reply: str):
    sess = _wa_sessions.setdefault(
        phone, {"history": [], "last_seen": datetime.now()})
    sess["history"].append({"user": user_msg, "bot": bot_reply})
    sess["last_seen"] = datetime.now()
    # Keep only last MAX_HISTORY turns
    if len(sess["history"]) > MAX_HISTORY:
        sess["history"] = sess["history"][-MAX_HISTORY:]


def _clear_session(phone: str):
    _wa_sessions.pop(phone, None)


# ══════════════════════════════════════════════════════════════
#  COMMAND ROUTER
# ══════════════════════════════════════════════════════════════

def _handle_command(text: str, phone: str, rag_chain, check_symptoms_fn, check_drug_fn) -> str:
    """
    Special commands handle karo.
    Returns response string ya None (if not a command).
    """
    t = text.strip()
    lower = t.lower()

    # /help
    if lower in ("/help", "help", "?", "commands"):
        return (
            "🏥 *MediBot Commands*\n\n"
            "💬 *Normal message* — Medical question poochho\n"
            "🩺 */symptoms* bukhar sir dard — Symptoms check karo\n"
            "⚗️ */drug* paracetamol vs ibuprofen — Drug interaction\n"
            "🔄 */reset* — Conversation reset karo\n"
            "❓ */help* — Ye message dobara dekho\n\n"
            "_Example: paracetamol kitni dose leni chahiye?_"
        )

    # /reset
    if lower in ("/reset", "reset", "clear"):
        _clear_session(phone)
        return "✅ Conversation reset ho gayi! Ab fresh start karein 🙏"

    # /symptoms <text>
    sym_match = re.match(r'^/symptoms?\s+(.+)', t, re.IGNORECASE)
    if sym_match:
        symptoms_text = sym_match.group(1)
        try:
            result = check_symptoms_fn(symptoms_text)
            return _format_symptom_result(result)
        except Exception as e:
            return f"❌ Symptom check mein error: {str(e)}"

    # /drug <A> vs <B>
    drug_match = re.match(
        r'^/drug\s+(.+?)\s+(?:vs|aur|and|,)\s+(.+)', t, re.IGNORECASE)
    if drug_match:
        drug_a = drug_match.group(1).strip()
        drug_b = drug_match.group(2).strip()
        try:
            result = check_drug_fn(drug_a, drug_b)
            return _format_drug_result(result)
        except Exception as e:
            return f"❌ Drug check mein error: {str(e)}"

    return None  # Not a command


# ══════════════════════════════════════════════════════════════
#  RESPONSE FORMATTERS (WhatsApp markdown: *bold* _italic_)
# ══════════════════════════════════════════════════════════════

def _format_symptom_result(result: dict) -> str:
    if not result.get("success") or not result.get("diseases"):
        return "🔍 In symptoms se koi match nahi mila.\n_Doctor se milein agar problem continue ho._"

    diseases = result["diseases"][:3]
    lines = ["🩺 *Symptom Analysis*\n"]
    for d in diseases:
        sev_icon = {"mild": "🟢", "moderate": "🟡",
                    "severe": "🔴"}.get(d.get("severity", ""), "⚪")
        lines.append(
            f"{sev_icon} *{d['disease']}* ({d.get('match_pct', 0):.0f}% match)")
        if d.get("advice"):
            lines.append(f"   💊 {d['advice']}")
        lines.append("")

    if result.get("see_doctor"):
        lines.append("⚠️ _Doctor se milna zaroori hai._")
    lines.append("\n_Yeh sirf AI analysis hai — professional advice nahi._")
    return "\n".join(lines)


def _format_drug_result(result: dict) -> str:
    if not result.get("success"):
        return f"❌ {result.get('error', 'Unknown error')}"

    icon = result.get("severity_icon", "ℹ️")
    label = result.get("severity_label", "")
    lines = [
        f"⚗️ *Drug Interaction Check*\n",
        f"💊 *{result['drug_a']}* + *{result['drug_b']}*\n",
        f"{icon} *{label}*\n",
    ]
    if result.get("summary"):
        lines.append(f"📋 {result['summary']}\n")
    if result.get("advice"):
        lines.append(f"✅ *Advice:* {result['advice']}")
    lines.append("\n_Doctor se zaroor milein._")
    return "\n".join(lines)


def _truncate(text: str, limit: int = 1500) -> str:
    """WhatsApp message 4096 chars max. Safe limit rakho."""
    if len(text) <= limit:
        return text
    return text[:limit] + "\n\n_...(answer lamba tha, website pe poora dekhein)_"


# ══════════════════════════════════════════════════════════════
#  MAIN HANDLER — called from app.py webhook route
# ══════════════════════════════════════════════════════════════

def handle_whatsapp_message(
    incoming_msg: str,
    from_number: str,
    rag_chain,
    check_symptoms_fn,
    check_drug_fn,
) -> str:
    """
    WhatsApp se aaya message process karo aur TwiML XML string return karo.

    Args:
        incoming_msg   : User ka message text
        from_number    : e.g. "whatsapp:+919876543210"
        rag_chain      : app.py ka LangChain RAG chain object
        check_symptoms_fn : symptom_checker.check_symptoms
        check_drug_fn  : drug_interaction.check_drug_interaction

    Returns:
        TwiML XML string (Flask Response mein dalna hai)
    """
    if not TWILIO_OK:
        return "<Response><Message>Twilio setup nahi hai.</Message></Response>"

    incoming_msg = (incoming_msg or "").strip()

    if not incoming_msg:
        reply = "🙏 Namaste! MediBot mein aapka swagat hai.\n*/help* type karein commands dekhne ke liye."
    else:
        # 1. Command check
        reply = _handle_command(incoming_msg, from_number,
                                rag_chain, check_symptoms_fn, check_drug_fn)

        # 2. RAG chain query
        if reply is None:
            try:
                history = _get_session(from_number)

                # Context banao pichle turns se
                context_prefix = ""
                if history:
                    recent = history[-2:]
                    context_prefix = "\n".join(
                        [f"User: {h['user']}\nBot: {h['bot']}" for h in recent]
                    ) + "\n\n"

                full_query = context_prefix + incoming_msg
                raw_reply = rag_chain.invoke(full_query)
                reply = str(raw_reply).strip()

                _save_to_session(from_number, incoming_msg, reply)
            except Exception as e:
                reply = f"❌ Error aaya: {str(e)}\n_Thodi der mein try karein._"

    reply = _truncate(reply)

    # Build TwiML response
    resp = MessagingResponse()
    resp.message(reply)
    return str(resp)


# ══════════════════════════════════════════════════════════════
#  TWILIO SIGNATURE VALIDATOR (security)
# ══════════════════════════════════════════════════════════════

def validate_twilio_signature(request_url: str, post_data: dict, signature: str) -> bool:
    """
    Twilio ka X-Twilio-Signature validate karo — fake requests block karo.
    Production mein ZAROOR use karo.
    """
    if not TWILIO_OK:
        return True  # Skip validation if twilio not installed

    auth_token = os.environ.get("TWILIO_AUTH_TOKEN", "")
    if not auth_token:
        return True  # No token configured, skip

    try:
        validator = RequestValidator(auth_token)
        return validator.validate(request_url, post_data, signature)
    except Exception:
        return False
