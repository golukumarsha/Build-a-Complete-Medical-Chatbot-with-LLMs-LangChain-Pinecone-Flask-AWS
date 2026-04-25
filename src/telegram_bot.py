# src/telegram_bot.py — MediBot Telegram Bot Integration
"""
python-telegram-bot v20+ (async) use karta hai.

Do modes available hain:
  A) POLLING — Local development ke liye. `run_telegram_polling()` call karo.
  B) WEBHOOK — Production ke liye. app.py /webhook/telegram route use karta hai.

Commands:
  /start          → Welcome message
  /help           → Available commands
  /symptoms <...> → Symptom checker
  /drug <A> vs <B>→ Drug interaction check
  /reset          → History clear
  /about          → MediBot info

Setup:
  1. Telegram pe @BotFather se bot banao
  2. /newbot → Name → Username → TOKEN milega
  3. .env mein TELEGRAM_BOT_TOKEN=<token> dalo
  4. Polling ke liye: python -m src.telegram_bot
  5. Webhook ke liye: app.py apne aap handle karta hai
"""

import os
import re
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ── python-telegram-bot ───────────────────────────────────────
try:
    from telegram import Update, Bot
    from telegram.ext import (
        Application, CommandHandler, MessageHandler,
        filters, ContextTypes
    )
    from telegram.constants import ParseMode, ChatAction
    TELEGRAM_OK = True
except ImportError:
    TELEGRAM_OK = False
    print("[Telegram] python-telegram-bot install nahi hai: pip install python-telegram-bot")

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

# ── Global RAG/function references (app.py se set honge) ──────
_rag_chain = None
_check_symptoms_fn = None
_check_drug_fn = None


def init_telegram_handlers(rag_chain, check_symptoms_fn, check_drug_fn):
    """
    app.py se call karo ek baar — references set ho jaate hain.
    """
    global _rag_chain, _check_symptoms_fn, _check_drug_fn
    _rag_chain = rag_chain
    _check_symptoms_fn = check_symptoms_fn
    _check_drug_fn = check_drug_fn


# ══════════════════════════════════════════════════════════════
#  SESSION STORE
# ══════════════════════════════════════════════════════════════
_tg_sessions: dict = {}
MAX_HISTORY = 6
SESSION_TTL_H = 6


def _get_history(user_id: int) -> list:
    now = datetime.now()
    sess = _tg_sessions.get(user_id)
    if sess:
        hrs = (now - sess["last_seen"]).total_seconds() / 3600
        if hrs < SESSION_TTL_H:
            sess["last_seen"] = now
            return sess["history"]
    _tg_sessions[user_id] = {"history": [], "last_seen": now}
    return _tg_sessions[user_id]["history"]


def _save_history(user_id: int, user_msg: str, bot_reply: str):
    sess = _tg_sessions.setdefault(
        user_id, {"history": [], "last_seen": datetime.now()})
    sess["history"].append({"user": user_msg, "bot": bot_reply})
    sess["last_seen"] = datetime.now()
    if len(sess["history"]) > MAX_HISTORY:
        sess["history"] = sess["history"][-MAX_HISTORY:]


def _clear_history(user_id: int):
    _tg_sessions.pop(user_id, None)


# ══════════════════════════════════════════════════════════════
#  RESPONSE FORMATTERS (Telegram MarkdownV2)
# ══════════════════════════════════════════════════════════════

def _md_escape(text: str) -> str:
    """MarkdownV2 special chars escape karo."""
    special = r'\_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(special)}])', r'\\\1', text)


def _format_symptom_tg(result: dict) -> str:
    if not result.get("success") or not result.get("diseases"):
        return "🔍 In symptoms se koi match nahi mila\\.\n_Doctor se milein agar takleef ho\\._"

    lines = ["🩺 *Symptom Analysis*\n"]
    for d in result["diseases"][:3]:
        icon = {"mild": "🟢", "moderate": "🟡", "severe": "🔴"}.get(
            d.get("severity", ""), "⚪")
        name = _md_escape(d['disease'])
        pct = d.get('match_pct', 0)
        lines.append(f"{icon} *{name}* \\({pct:.0f}% match\\)")
        if d.get("advice"):
            lines.append(f"  💊 {_md_escape(d['advice'])}")
        lines.append("")

    if result.get("see_doctor"):
        lines.append("⚠️ _Doctor se milna zaroori hai\\._")
    lines.append("\n_Sirf AI analysis hai — professional advice nahi\\._")
    return "\n".join(lines)


def _format_drug_tg(result: dict) -> str:
    if not result.get("success"):
        return f"❌ {_md_escape(result.get('error', 'Unknown error'))}"

    icon = result.get("severity_icon", "ℹ️")
    label = _md_escape(result.get("severity_label", ""))
    da = _md_escape(result["drug_a"])
    db = _md_escape(result["drug_b"])
    lines = [
        f"⚗️ *Drug Interaction*\n",
        f"💊 *{da}* \\+ *{db}*\n",
        f"{icon} *{label}*\n",
    ]
    if result.get("summary"):
        lines.append(_md_escape(result["summary"]))
    if result.get("advice"):
        lines.append(f"\n✅ *Advice:* {_md_escape(result['advice'])}")
    lines.append("\n_Doctor se zaroor milein\\._")
    return "\n".join(lines)


def _truncate(text: str, limit: int = 3800) -> str:
    """Telegram 4096 char limit."""
    if len(text) <= limit:
        return text
    return text[:limit] + "\n\n_\\.\\.\\. answer lamba tha, website pe dekhein_"


# ══════════════════════════════════════════════════════════════
#  COMMAND HANDLERS
# ══════════════════════════════════════════════════════════════

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name or "Friend"
    await update.message.reply_text(
        f"🏥 *Namaste {_md_escape(name)}\\!*\n\n"
        "Main *MediBot* hoon — aapka AI Medical Assistant\\.\n\n"
        "Medical questions poochho, symptoms check karo, ya drug interactions jaano\\.\n\n"
        "*/help* type karein sab commands dekhne ke liye 🙏",
        parse_mode=ParseMode.MARKDOWN_V2,
    )


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏥 *MediBot — Commands*\n\n"
        "💬 *Normal message* — Medical question poochho\n"
        "🩺 */symptoms* bukhar sar dard — Symptoms check\n"
        "⚗️ */drug* paracetamol vs ibuprofen — Interaction check\n"
        "🔄 */reset* — Conversation reset karo\n"
        "ℹ️ */about* — MediBot ke baare mein\n\n"
        "_Example:_ paracetamol kitni dose leni chahiye\\?",
        parse_mode=ParseMode.MARKDOWN_V2,
    )


async def cmd_about(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *MediBot — About*\n\n"
        "MediBot ek AI\\-powered medical assistant hai jo use karta hai:\n"
        "• *Groq LLaMA 3\\.1* — Fast AI responses\n"
        "• *Pinecone RAG* — Medical knowledge base\n"
        "• *Scikit\\-learn* — Symptom checker\n"
        "• *RxNorm \\+ OpenFDA* — Drug interactions\n\n"
        "🌐 Website: /web ka link yahan add karein\n"
        "⚕️ _Disclaimer: Sirf informational purpose ke liye\\._",
        parse_mode=ParseMode.MARKDOWN_V2,
    )


async def cmd_reset(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    _clear_history(update.effective_user.id)
    await update.message.reply_text("✅ Conversation reset ho gayi\\! Fresh start karein 🙏", parse_mode=ParseMode.MARKDOWN_V2)


async def cmd_symptoms(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text(
            "🩺 Symptoms batao\\:\n`/symptoms bukhar sar dard thakaan`",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    text = " ".join(ctx.args)
    await update.message.chat.send_action(ChatAction.TYPING)
    try:
        result = _check_symptoms_fn(text)
        reply = _format_symptom_tg(result)
    except Exception as e:
        reply = f"❌ Error: {_md_escape(str(e))}"

    await update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN_V2)


async def cmd_drug(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args or len(ctx.args) < 3:
        await update.message.reply_text(
            "⚗️ Format:\n`/drug medicine1 vs medicine2`\n\nExample:\n`/drug warfarin vs aspirin`",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    full = " ".join(ctx.args)
    match = re.search(r'(.+?)\s+(?:vs|aur|and|,)\s+(.+)', full, re.IGNORECASE)
    if not match:
        await update.message.reply_text("Format galat hai\\. Example: `/drug paracetamol vs ibuprofen`", parse_mode=ParseMode.MARKDOWN_V2)
        return

    drug_a, drug_b = match.group(1).strip(), match.group(2).strip()
    await update.message.chat.send_action(ChatAction.TYPING)
    try:
        result = _check_drug_fn(drug_a, drug_b)
        reply = _format_drug_tg(result)
    except Exception as e:
        reply = f"❌ Error: {_md_escape(str(e))}"

    await update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN_V2)


# ══════════════════════════════════════════════════════════════
#  GENERAL MESSAGE HANDLER (RAG chain)
# ══════════════════════════════════════════════════════════════

async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_msg = (update.message.text or "").strip()
    if not user_msg:
        return

    await update.message.chat.send_action(ChatAction.TYPING)

    try:
        history = _get_history(user_id)
        context_prefix = ""
        if history:
            recent = history[-2:]
            context_prefix = "\n".join(
                [f"User: {h['user']}\nBot: {h['bot']}" for h in recent]
            ) + "\n\n"

        full_query = context_prefix + user_msg
        raw_reply = await asyncio.get_event_loop().run_in_executor(
            None, _rag_chain.invoke, full_query
        )
        reply = str(raw_reply).strip()
        _save_history(user_id, user_msg, reply)

    except Exception as e:
        reply = f"❌ Error aaya: {str(e)}\nThodi der mein try karein."

    reply = _truncate(reply)
    # Send as plain text (RAG output may have formatting issues with MarkdownV2)
    await update.message.reply_text(reply)


# ══════════════════════════════════════════════════════════════
#  WEBHOOK HANDLER — called from app.py /webhook/telegram route
# ══════════════════════════════════════════════════════════════

async def process_telegram_update(update_json: dict):
    """
    app.py webhook route se call hota hai.
    Update JSON dict pass karo — bot process karega.
    """
    if not TELEGRAM_OK or not TELEGRAM_TOKEN:
        return

    app = _get_or_build_app()
    update = Update.de_json(update_json, app.bot)
    await app.process_update(update)


_tg_app = None


def _get_or_build_app():
    """Singleton Application instance — ek baar build, baar baar use."""
    global _tg_app
    if _tg_app is None:
        _tg_app = _build_app()
    return _tg_app


def _build_app() -> "Application":
    """Handlers register karo aur Application return karo."""
    builder = Application.builder().token(TELEGRAM_TOKEN)
    application = builder.build()

    application.add_handler(CommandHandler("start",    cmd_start))
    application.add_handler(CommandHandler("help",     cmd_help))
    application.add_handler(CommandHandler("about",    cmd_about))
    application.add_handler(CommandHandler("reset",    cmd_reset))
    application.add_handler(CommandHandler("symptoms", cmd_symptoms))
    application.add_handler(CommandHandler("drug",     cmd_drug))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    return application


# ══════════════════════════════════════════════════════════════
#  POLLING MODE — local development
#  Run: python -m src.telegram_bot
# ══════════════════════════════════════════════════════════════

def run_telegram_polling(rag_chain, check_symptoms_fn, check_drug_fn):
    """
    Local development ke liye polling mode.
    app.py se alag process mein chalta hai.

    Usage (app.py ke saath parallel):
        from src.telegram_bot import run_telegram_polling
        import threading
        t = threading.Thread(target=run_telegram_polling, args=(rag_chain, check_symptoms, check_drug_interaction), daemon=True)
        t.start()
    """
    if not TELEGRAM_OK:
        print("[Telegram] python-telegram-bot install nahi hai!")
        return
    if not TELEGRAM_TOKEN:
        print("[Telegram] TELEGRAM_BOT_TOKEN .env mein set nahi hai!")
        return

    init_telegram_handlers(rag_chain, check_symptoms_fn, check_drug_fn)
    application = _build_app()

    print("🤖 Telegram Bot polling start ho raha hai...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


# Direct execution
if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from dotenv import load_dotenv
    load_dotenv()
    print("⚠️  Direct run ke liye app.py se rag_chain chahiye.")
    print("    app.py mein TELEGRAM_POLLING=true set karein.")
