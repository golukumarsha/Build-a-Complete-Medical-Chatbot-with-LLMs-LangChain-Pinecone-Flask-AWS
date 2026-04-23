# app.py — MediBot: Groq + RAG + Medical Image + MongoDB
from src.image_helper import get_medical_image
from src.helper import download_hugging_face_embeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os
import certifi

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

load_dotenv()


# ── MongoDB optional — crash nahi hoga agar MongoDB nahi hai ──
try:
    from src.database import (
        save_search_log, get_search_logs, get_search_stats, delete_all_logs,
        search_medicine, get_all_medicines, get_by_category, get_stats,
        insert_medicine, update_medicine, delete_medicine,
    )
    MONGO_AVAILABLE = True
    print("✅ MongoDB connected!")
except Exception as mongo_err:
    MONGO_AVAILABLE = False
    print(
        f"⚠️  MongoDB nahi mila — chatbot bina MongoDB ke bhi chalega!\n   Error: {mongo_err}")

app = Flask(__name__)

# ── Keys ─────────────────────────────────────────────────────
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# ── Embeddings + Pinecone ─────────────────────────────────────
embeddings = download_hugging_face_embeddings()
pc = Pinecone(api_key=PINECONE_API_KEY)
docsearch = PineconeVectorStore.from_existing_index(
    index_name="medical-chatbot",
    embedding=embeddings
)
retriever = docsearch.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3}
)

# ── Groq LLM ──────────────────────────────────────────────────
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=GROQ_API_KEY,
    temperature=0.4,
    max_tokens=800
)

# ── System Prompt — Hindi + English dono support ─────────────
# SABSE IMPORTANT FIX: Hindi mein pooche to Hindi mein jawab
system_prompt = """You are MediBot — an expert AI Medical Assistant.

STRICT LANGUAGE RULE (follow karna zaroori hai):
- Agar user HINDI ya HINGLISH mein pooche → tum HINDI mein jawab do
- Agar user ENGLISH mein pooche → tum ENGLISH mein jawab do
- User ki language exactly match karo, kabhi mat badlo

Use the context below to answer accurately:
{context}

Instructions:
- Sirf medical facts batao jo context mein hain
- Agar context mein answer nahi hai, apni general medical knowledge use karo
- Answer clear aur helpful hona chahiye (3-5 sentences)
- Koi unnecessary disclaimer mat do
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
])


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


# ── RAG Chain ─────────────────────────────────────────────────
rag_chain = (
    {"context": retriever | format_docs, "input": RunnablePassthrough()}
    | prompt | llm | StrOutputParser()
)


# ═══════════════════════════════════════════════════════════════
#  PAGES
# ═══════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return render_template("chat.html")


@app.route("/medicines")
def medicines_page():
    if not MONGO_AVAILABLE:
        return """<div style='font-family:sans-serif;text-align:center;padding:40px;background:#070f18;color:#d6eeff;min-height:100vh'>
            <h2 style='color:#ff6b6b'>⚠️ MongoDB Connected Nahi Hai</h2>
            <p>Pehle MongoDB install karein ya Atlas connect karein</p>
            <a href='/' style='color:#00d9a0'>← Chatbot pe wapas jao</a></div>"""
    return render_template("medicines.html")


@app.route("/history")
def history_page():
    if not MONGO_AVAILABLE:
        return """<div style='font-family:sans-serif;text-align:center;padding:40px;background:#070f18;color:#d6eeff;min-height:100vh'>
            <h2 style='color:#ff6b6b'>⚠️ MongoDB Connected Nahi Hai</h2>
            <p>Pehle MongoDB install karein ya Atlas connect karein</p>
            <a href='/' style='color:#00d9a0'>← Chatbot pe wapas jao</a></div>"""
    return render_template("history.html")


# ═══════════════════════════════════════════════════════════════
#  CHAT API
# ═══════════════════════════════════════════════════════════════

@app.route("/get", methods=["POST"])
def chat():
    try:
        msg = request.form["msg"]

        # 1. RAG se AI answer — Hindi ya English mein
        response_text = rag_chain.invoke(msg)

        # 2. Wikipedia/Unsplash image
        image_data = get_medical_image(msg)

        # 3. MongoDB se medicine match + log save (optional)
        db_info = None
        if MONGO_AVAILABLE:
            try:
                db_results = search_medicine(msg)
                db_info = db_results[0] if db_results else None
                save_search_log(
                    query=msg,
                    ai_response=str(response_text),
                    matched_medicine=db_info["name"] if db_info else None,
                    image_found=bool(
                        image_data and image_data.get("image_url"))
                )
            except Exception as db_err:
                print(f"[DB Warning] {db_err}")

        return jsonify({
            "response": str(response_text),
            "image":    image_data,
            "db_info":  db_info
        })

    except Exception as e:
        return jsonify({
            "response": f"❌ Error aaya: {str(e)}",
            "image":    None,
            "db_info":  None
        }), 500


# ═══════════════════════════════════════════════════════════════
#  SEARCH LOG API
# ═══════════════════════════════════════════════════════════════

@app.route("/api/logs", methods=["GET"])
def api_get_logs():
    if not MONGO_AVAILABLE:
        return jsonify({"success": False, "error": "MongoDB nahi mila"}), 503
    try:
        limit = int(request.args.get("limit", 50))
        logs = get_search_logs(limit=limit)
        return jsonify({"success": True, "count": len(logs), "data": logs})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/logs/stats", methods=["GET"])
def api_log_stats():
    if not MONGO_AVAILABLE:
        return jsonify({"success": False, "error": "MongoDB nahi mila"}), 503
    try:
        return jsonify({"success": True, "data": get_search_stats()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/logs", methods=["DELETE"])
def api_clear_logs():
    if not MONGO_AVAILABLE:
        return jsonify({"success": False, "error": "MongoDB nahi mila"}), 503
    try:
        result = delete_all_logs()
        return jsonify({"success": True, "message": f"{result['deleted']} logs delete ho gaye!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ═══════════════════════════════════════════════════════════════
#  MEDICINES API
# ═══════════════════════════════════════════════════════════════

@app.route("/api/medicines", methods=["GET"])
def api_get_medicines():
    if not MONGO_AVAILABLE:
        return jsonify({"success": False, "error": "MongoDB nahi mila"}), 503
    try:
        category = request.args.get("category")
        data = get_by_category(category) if category else get_all_medicines()
        return jsonify({"success": True, "count": len(data), "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/medicines/search", methods=["GET"])
def api_search():
    if not MONGO_AVAILABLE:
        return jsonify({"success": False, "error": "MongoDB nahi mila"}), 503
    try:
        q = request.args.get("q", "")
        if not q:
            return jsonify({"success": False, "error": "Query 'q' required"}), 400
        results = search_medicine(q)
        return jsonify({"success": True, "count": len(results), "data": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/medicines/stats", methods=["GET"])
def api_stats():
    if not MONGO_AVAILABLE:
        return jsonify({"success": True, "data": {
            "total": 0, "diseases": 0, "medicines": 0, "supplements": 0
        }})
    try:
        return jsonify({"success": True, "data": get_stats()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/medicines", methods=["POST"])
def api_add_medicine():
    if not MONGO_AVAILABLE:
        return jsonify({"success": False, "error": "MongoDB nahi mila"}), 503
    try:
        data = request.get_json()
        if not data or not data.get("name"):
            return jsonify({"success": False, "error": "'name' required"}), 400
        result = insert_medicine(data)
        return jsonify(result), 201 if result["success"] else 409
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/medicines/<n>", methods=["PUT"])
def api_update(n):
    if not MONGO_AVAILABLE:
        return jsonify({"success": False, "error": "MongoDB nahi mila"}), 503
    try:
        result = update_medicine(n, request.get_json())
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/medicines/<n>", methods=["DELETE"])
def api_delete(n):
    if not MONGO_AVAILABLE:
        return jsonify({"success": False, "error": "MongoDB nahi mila"}), 503
    try:
        result = delete_medicine(n)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ═══════════════════════════════════════════════════════════════
#  HEALTH CHECK
# ═══════════════════════════════════════════════════════════════

@app.route("/health")
def health():
    status = {
        "status":   "healthy",
        "db":       "connected" if MONGO_AVAILABLE else "disconnected",
        "pinecone": "connected",
        "groq":     "connected",
    }
    if MONGO_AVAILABLE:
        try:
            s = get_stats()
            ls = get_search_stats()
            status["medicines"] = s["total"]
            status["total_searches"] = ls["total_searches"]
        except Exception:
            pass
    return jsonify(status)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
