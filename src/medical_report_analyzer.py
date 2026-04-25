# src/medical_report_analyzer.py — Medical PDF Report Analyzer for MediBot
"""
Flow:
  User PDF upload → PyPDF2 se text extract → LangChain chain → Groq LLM
  → Values identify → Simple Hindi/English explanation generate

Supports:
  - Blood test reports (CBC, LFT, KFT, Thyroid, Sugar, Lipid)
  - General lab reports
  - Discharge summaries
  - Any medical PDF
"""

import re
import os
import io
from datetime import datetime

# ── PDF Extraction ──────────────────────────────────────────────
try:
    import PyPDF2
    PYPDF2_OK = True
except ImportError:
    try:
        from pypdf import PdfReader as PyPDF2_Reader
        PYPDF2_OK = True
    except ImportError:
        PYPDF2_OK = False

# ── LangChain + Groq ───────────────────────────────────────────
try:
    from langchain_groq import ChatGroq
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    LANGCHAIN_OK = True
except ImportError:
    LANGCHAIN_OK = False


# ══════════════════════════════════════════════════════════════
#  KNOWN BLOOD TEST PARAMETERS — normal ranges
# ══════════════════════════════════════════════════════════════
NORMAL_RANGES = {
    # CBC
    "hemoglobin":        {"min": 12.0, "max": 17.5, "unit": "g/dL",  "label": "Hemoglobin (Hb)"},
    "hb":                {"min": 12.0, "max": 17.5, "unit": "g/dL",  "label": "Hemoglobin (Hb)"},
    "wbc":               {"min": 4.0,  "max": 11.0, "unit": "K/µL",  "label": "White Blood Cells"},
    "rbc":               {"min": 4.2,  "max": 5.9,  "unit": "M/µL",  "label": "Red Blood Cells"},
    "platelets":         {"min": 150,  "max": 400,  "unit": "K/µL",  "label": "Platelets"},
    "hematocrit":        {"min": 36.0, "max": 50.0, "unit": "%",     "label": "Hematocrit (PCV)"},

    # Blood Sugar
    "glucose":           {"min": 70,   "max": 100,  "unit": "mg/dL", "label": "Blood Glucose (Fasting)"},
    "fasting glucose":   {"min": 70,   "max": 100,  "unit": "mg/dL", "label": "Fasting Glucose"},
    "hba1c":             {"min": 4.0,  "max": 5.6,  "unit": "%",     "label": "HbA1c"},
    "pp glucose":        {"min": 70,   "max": 140,  "unit": "mg/dL", "label": "PP Glucose"},

    # Lipid Profile
    "cholesterol":       {"min": 0,    "max": 200,  "unit": "mg/dL", "label": "Total Cholesterol"},
    "ldl":               {"min": 0,    "max": 100,  "unit": "mg/dL", "label": "LDL Cholesterol"},
    "hdl":               {"min": 40,   "max": 999,  "unit": "mg/dL", "label": "HDL Cholesterol"},
    "triglycerides":     {"min": 0,    "max": 150,  "unit": "mg/dL", "label": "Triglycerides"},
    "vldl":              {"min": 0,    "max": 30,   "unit": "mg/dL", "label": "VLDL"},

    # Kidney (KFT)
    "creatinine":        {"min": 0.6,  "max": 1.3,  "unit": "mg/dL", "label": "Creatinine"},
    "urea":              {"min": 7,    "max": 20,   "unit": "mg/dL", "label": "Blood Urea"},
    "bun":               {"min": 7,    "max": 20,   "unit": "mg/dL", "label": "BUN (Blood Urea Nitrogen)"},
    "uric acid":         {"min": 2.6,  "max": 7.2,  "unit": "mg/dL", "label": "Uric Acid"},

    # Liver (LFT)
    "sgpt":              {"min": 7,    "max": 40,   "unit": "U/L",   "label": "SGPT (ALT)"},
    "alt":               {"min": 7,    "max": 40,   "unit": "U/L",   "label": "ALT (SGPT)"},
    "sgot":              {"min": 10,   "max": 40,   "unit": "U/L",   "label": "SGOT (AST)"},
    "ast":               {"min": 10,   "max": 40,   "unit": "U/L",   "label": "AST (SGOT)"},
    "bilirubin":         {"min": 0.1,  "max": 1.2,  "unit": "mg/dL", "label": "Total Bilirubin"},
    "alkaline phosphatase": {"min": 44, "max": 147, "unit": "U/L",  "label": "Alkaline Phosphatase"},
    "alp":               {"min": 44,   "max": 147,  "unit": "U/L",   "label": "ALP"},

    # Thyroid
    "tsh":               {"min": 0.4,  "max": 4.0,  "unit": "µIU/mL", "label": "TSH (Thyroid)"},
    "t3":                {"min": 80,   "max": 200,  "unit": "ng/dL", "label": "T3 (Triiodothyronine)"},
    "t4":                {"min": 5.0,  "max": 12.0, "unit": "µg/dL", "label": "T4 (Thyroxine)"},

    # Vitamins & Minerals
    "vitamin d":         {"min": 30,   "max": 100,  "unit": "ng/mL", "label": "Vitamin D"},
    "vitamin b12":       {"min": 200,  "max": 900,  "unit": "pg/mL", "label": "Vitamin B12"},
    "iron":              {"min": 60,   "max": 170,  "unit": "µg/dL", "label": "Serum Iron"},
    "ferritin":          {"min": 12,   "max": 300,  "unit": "ng/mL", "label": "Ferritin"},
    "calcium":           {"min": 8.5,  "max": 10.5, "unit": "mg/dL", "label": "Calcium"},
    "sodium":            {"min": 136,  "max": 145,  "unit": "mEq/L", "label": "Sodium"},
    "potassium":         {"min": 3.5,  "max": 5.0,  "unit": "mEq/L", "label": "Potassium"},
}


# ══════════════════════════════════════════════════════════════
#  STEP 1: PDF → Text extract
# ══════════════════════════════════════════════════════════════
def extract_text_from_pdf(file_bytes: bytes) -> str:
    """PyPDF2 se PDF ka text extract karo."""
    if not PYPDF2_OK:
        raise ImportError("PyPDF2 install nahi hai: pip install PyPDF2")

    try:
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        text_parts = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
        full_text = "\n".join(text_parts)
        return full_text.strip()
    except Exception as e:
        raise ValueError(f"PDF read nahi ho saka: {str(e)}")


# ══════════════════════════════════════════════════════════════
#  STEP 2: Local value extraction (regex-based, fast)
# ══════════════════════════════════════════════════════════════
def extract_values_locally(text: str) -> list:
    """
    PDF text mein se numeric values dhundho aur normal range se compare karo.
    Returns list of dicts with status: normal/high/low/critical
    """
    found = []
    text_lower = text.lower()

    # Regex: "parameter name ... number ... unit"
    number_pattern = re.compile(
        r'([\d]+\.?\d*)\s*(g/dl|mg/dl|u/l|k/µl|m/µl|%|µiu/ml|ng/ml|pg/ml|µg/dl|meq/l|ng/dl|iu/l)?',
        re.IGNORECASE
    )

    for key, ref in NORMAL_RANGES.items():
        # Check if this parameter name appears in text
        if key not in text_lower:
            continue

        # Find the line containing this parameter
        for line in text.split('\n'):
            if key in line.lower():
                # Extract number from this line
                nums = re.findall(r'\b(\d+\.?\d*)\b', line)
                if not nums:
                    continue

                # Take the most "reasonable" number
                val = None
                for n in nums:
                    candidate = float(n)
                    # Skip obviously wrong values (like years, page numbers etc.)
                    if ref["min"] * 0.1 <= candidate <= ref["max"] * 10:
                        val = candidate
                        break

                if val is None:
                    continue

                # Compare with normal range
                r_min, r_max = ref["min"], ref["max"]
                if val < r_min:
                    if val < r_min * 0.7:
                        status = "critical_low"
                    else:
                        status = "low"
                elif val > r_max:
                    if val > r_max * 1.5:
                        status = "critical_high"
                    else:
                        status = "high"
                else:
                    status = "normal"

                found.append({
                    "parameter": ref["label"],
                    "key":       key,
                    "value":     val,
                    "unit":      ref["unit"],
                    "min":       r_min,
                    "max":       r_max,
                    "status":    status,
                })
                break  # Only first match per parameter

    # Deduplicate by parameter label
    seen = set()
    unique = []
    for item in found:
        if item["parameter"] not in seen:
            seen.add(item["parameter"])
            unique.append(item)

    return unique


# ══════════════════════════════════════════════════════════════
#  STEP 3: AI Explanation via LangChain + Groq
# ══════════════════════════════════════════════════════════════

REPORT_SYSTEM_PROMPT = """You are MediBot — an expert Medical Report Explainer.

Your job is to read a patient's medical report text and explain it in SIMPLE language.

LANGUAGE RULE (STRICTLY FOLLOW):
- Agar report ya user ki request Hindi/Hinglish mein hai → Hindi mein explain karo
- If report is in English and no Hindi hint → Explain in English
- Always use simple words, avoid complex medical jargon

WHAT TO DO:
1. Identify the type of report (Blood test / X-ray / Discharge summary etc.)
2. List ALL abnormal values you find (HIGH or LOW) — these are most important
3. For each abnormal value, explain in 1-2 simple sentences what it means
4. Give an OVERALL SUMMARY in 3-4 lines
5. Give ACTIONABLE ADVICE — what should the patient do next
6. Add a disclaimer at the end

FORMAT YOUR RESPONSE AS:
📋 REPORT TYPE: [type]

⚠️ ABNORMAL VALUES:
[list each one clearly]

✅ NORMAL VALUES:
[briefly mention what's normal]

📊 OVERALL SUMMARY:
[3-4 lines]

💊 WHAT TO DO NEXT:
[clear actionable advice]

⚕️ DISCLAIMER: Yeh AI-based analysis hai. Apne doctor se zaroor milein.

REPORT TEXT:
{report_text}
"""


def analyze_with_ai(report_text: str, groq_api_key: str = None) -> str:
    """LangChain + Groq se full AI analysis generate karo."""
    if not LANGCHAIN_OK:
        return "❌ LangChain install nahi hai."

    api_key = groq_api_key or os.environ.get("GROQ_API_KEY")
    if not api_key:
        return "❌ GROQ_API_KEY nahi mila."

    # Limit text to avoid token overflow
    report_text_trimmed = report_text[:4000] if len(
        report_text) > 4000 else report_text

    try:
        llm = ChatGroq(
            model="llama-3.1-8b-instant",
            api_key=api_key,
            temperature=0.3,
            max_tokens=1200,
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", REPORT_SYSTEM_PROMPT),
            ("human", "Please analyze this medical report and explain it clearly.")
        ])

        chain = prompt | llm | StrOutputParser()
        result = chain.invoke({"report_text": report_text_trimmed})
        return result

    except Exception as e:
        return f"❌ AI analysis mein error: {str(e)}"


# ══════════════════════════════════════════════════════════════
#  MAIN FUNCTION — called from app.py route
# ══════════════════════════════════════════════════════════════
def analyze_medical_report(file_bytes: bytes, filename: str = "") -> dict:
    """
    Main entry point.

    Returns:
    {
        "success": True/False,
        "filename": "...",
        "page_count": N,
        "extracted_text_preview": "...",
        "local_values": [...],        # regex-extracted values with status
        "ai_analysis": "...",         # full LLM explanation
        "abnormal_count": N,
        "critical_count": N,
        "normal_count": N,
        "analyzed_at": "..."
    }
    """
    result = {
        "success":                False,
        "filename":               filename,
        "page_count":             0,
        "extracted_text_preview": "",
        "local_values":           [],
        "ai_analysis":            "",
        "abnormal_count":         0,
        "critical_count":         0,
        "normal_count":           0,
        "analyzed_at":            datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "error":                  None,
    }

    # ── Extract text ──────────────────────────────────────────
    try:
        raw_text = extract_text_from_pdf(file_bytes)
    except Exception as e:
        result["error"] = str(e)
        return result

    if not raw_text or len(raw_text) < 30:
        result["error"] = "PDF mein readable text nahi mila. Scanned image PDF hai? Text-based PDF upload karein."
        return result

    # Page count estimate
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        result["page_count"] = len(reader.pages)
    except Exception:
        result["page_count"] = 1

    result["extracted_text_preview"] = raw_text[:500] + \
        ("..." if len(raw_text) > 500 else "")

    # ── Local value extraction ─────────────────────────────────
    local_vals = extract_values_locally(raw_text)
    result["local_values"] = local_vals

    abnormal = [v for v in local_vals if v["status"] in ("high", "low")]
    critical = [v for v in local_vals if "critical" in v["status"]]
    normal = [v for v in local_vals if v["status"] == "normal"]

    result["abnormal_count"] = len(abnormal) + len(critical)
    result["critical_count"] = len(critical)
    result["normal_count"] = len(normal)

    # ── AI Analysis ────────────────────────────────────────────
    ai_text = analyze_with_ai(raw_text)
    result["ai_analysis"] = ai_text

    result["success"] = True
    return result
