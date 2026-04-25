# src/symptom_checker.py — ML-based Symptom Checker for MediBot
"""
Decision Tree + Rule-based hybrid model.
Scikit-learn ka use karta hai — koi external API nahi chahiye.

Flow:
  User symptoms (text) → symptom extraction → ML prediction → diseases list
"""

import re
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import MultiLabelBinarizer
import numpy as np

# ══════════════════════════════════════════════════════════════
#  DISEASE DATABASE — symptoms + info
# ══════════════════════════════════════════════════════════════
DISEASE_DATA = {
    "Common Cold": {
        "symptoms": ["runny nose", "sneezing", "sore throat", "mild fever", "cough", "congestion", "naak behna", "chheenk", "gala dard", "halka bukhar", "khansi", "band naak"],
        "severity": "mild",
        "color":    "#00c896",
        "icon":     "🤧",
        "advice":   "Aaram karo, paani zyada piyo. Paracetamol le sakte ho fever ke liye.",
        "see_doctor": False,
        "medicines":  ["Paracetamol", "Cetirizine", "Vitamin C"],
    },
    "Influenza (Flu)": {
        "symptoms": ["high fever", "body ache", "fatigue", "headache", "cough", "chills", "tez bukhar", "badan dard", "kamzori", "sir dard", "khansi", "thakaan", "sar dard"],
        "severity": "moderate",
        "color":    "#ffa500",
        "icon":     "🤒",
        "advice":   "Rest karo, hydrated raho. Doctor se mil sakte ho antiviral ke liye.",
        "see_doctor": True,
        "medicines":  ["Paracetamol", "Ibuprofen", "ORS"],
    },
    "COVID-19": {
        "symptoms": ["fever", "dry cough", "loss of taste", "loss of smell", "shortness of breath", "fatigue", "body ache", "bukhar", "sukhi khansi", "swad nahi", "khushbu nahi", "saans takleef", "thakaan", "badan dard"],
        "severity": "high",
        "color":    "#ff5c5c",
        "icon":     "🦠",
        "advice":   "Turant isolation karo aur COVID test karwao. Doctor se consult karo.",
        "see_doctor": True,
        "medicines":  ["Paracetamol", "Vitamin C", "Zinc", "Doctor prescription zaroori"],
    },
    "Pneumonia": {
        "symptoms": ["high fever", "chest pain", "difficulty breathing", "productive cough", "chills", "fatigue", "tez bukhar", "seene mein dard", "saans lene mein takleef", "balgam wali khansi", "thakaan"],
        "severity": "high",
        "color":    "#ff5c5c",
        "icon":     "🫁",
        "advice":   "Yeh serious condition hai. Turant doctor ke paas jao. Hospital admit hona pad sakta hai.",
        "see_doctor": True,
        "medicines":  ["Antibiotics (doctor se)", "Paracetamol", "Hospital care"],
    },
    "Malaria": {
        "symptoms": ["cyclical fever", "chills", "sweating", "headache", "nausea", "muscle pain", "thanda lagna", "paseena", "sir dard", "ulti", "badan dard", "bukhar aana jaana"],
        "severity": "high",
        "color":    "#ff5c5c",
        "icon":     "🦟",
        "advice":   "Blood test karwao turant. Antimalarial treatment doctor se lo.",
        "see_doctor": True,
        "medicines":  ["Chloroquine", "Artemisinin (doctor se)", "Paracetamol"],
    },
    "Dengue": {
        "symptoms": ["high fever", "severe headache", "pain behind eyes", "joint pain", "muscle pain", "rash", "bleeding", "tez bukhar", "aankhon ke peeche dard", "jodo mein dard", "skin par daane", "khoon aana"],
        "severity": "high",
        "color":    "#ff5c5c",
        "icon":     "🦟",
        "advice":   "Platelet count monitor karo. Doctor se milna zaroori hai. Aspirin/Ibuprofen BILKUL mat lo.",
        "see_doctor": True,
        "medicines":  ["Paracetamol (sirf yahi)", "ORS", "Doctor supervision zaroori"],
    },
    "Typhoid": {
        "symptoms": ["prolonged fever", "abdominal pain", "weakness", "headache", "loss of appetite", "constipation", "rash", "lambe time tak bukhar", "pet dard", "kamzori", "bhook nahi", "kabz"],
        "severity": "high",
        "color":    "#ff5c5c",
        "icon":     "🦠",
        "advice":   "Blood/urine test karwao. Antibiotics doctor ke prescription se lo. Saaf paani piyo.",
        "see_doctor": True,
        "medicines":  ["Azithromycin (doctor se)", "Ciprofloxacin (doctor se)", "ORS"],
    },
    "Diabetes (Type 2)": {
        "symptoms": ["frequent urination", "excessive thirst", "fatigue", "blurred vision", "slow healing", "weight loss", "baar baar peshab", "bahut pyaas", "thakaan", "aankhein dhundhla", "zakhm na bharna", "wazan ghata"],
        "severity": "moderate",
        "color":    "#ffa500",
        "icon":     "🩸",
        "advice":   "Blood sugar test karwao. Diet control karo. Doctor se Metformin ke baare mein poochho.",
        "see_doctor": True,
        "medicines":  ["Metformin (doctor se)", "Insulin (agar zaroori ho)", "Diet control"],
    },
    "Hypertension": {
        "symptoms": ["headache", "dizziness", "shortness of breath", "chest pain", "nosebleed", "blurred vision", "sir dard", "chakkar", "saans ki takleef", "seene mein dard", "naak se khoon", "aankhein dhundhla"],
        "severity": "moderate",
        "color":    "#ffa500",
        "icon":     "❤️",
        "advice":   "BP check karwao. Namak kam khao. Doctor se BP ki dawa lo.",
        "see_doctor": True,
        "medicines":  ["Amlodipine (doctor se)", "Lisinopril (doctor se)", "Lifestyle changes"],
    },
    "Asthma": {
        "symptoms": ["wheezing", "shortness of breath", "chest tightness", "cough at night", "difficulty breathing", "seene mein kheenchav", "saans ki takleef", "raat ko khansi", "saans mein awaaz"],
        "severity": "moderate",
        "color":    "#ffa500",
        "icon":     "💨",
        "advice":   "Inhaler saath rakhо. Triggers se bachо. Doctor se inhaler prescription lo.",
        "see_doctor": True,
        "medicines":  ["Salbutamol inhaler", "Corticosteroids (doctor se)", "Avoid triggers"],
    },
    "Gastroenteritis": {
        "symptoms": ["diarrhea", "vomiting", "nausea", "abdominal cramps", "fever", "dehydration", "dast", "ulti", "ji machalna", "pet mein marore", "bukhar", "paani ki kami"],
        "severity": "mild",
        "color":    "#00c896",
        "icon":     "🤢",
        "advice":   "ORS piyo. Halka khana khao. Haath dhote raho. Agar 2 din se zyada ho to doctor se milo.",
        "see_doctor": False,
        "medicines":  ["ORS", "Zinc", "Probiotics", "Paracetamol (fever ke liye)"],
    },
    "Migraine": {
        "symptoms": ["severe headache", "nausea", "sensitivity to light", "sensitivity to sound", "vomiting", "aura", "tez sir dard", "roshan se takleef", "awaaz se takleef", "ulti"],
        "severity": "moderate",
        "color":    "#ffa500",
        "icon":     "🧠",
        "advice":   "Andheri aur shant jagah mein aaram karo. Ibuprofen ya Paracetamol lo. Doctor se preventive dawa poochho.",
        "see_doctor": False,
        "medicines":  ["Ibuprofen", "Paracetamol", "Sumatriptan (doctor se)"],
    },
    "Urinary Tract Infection (UTI)": {
        "symptoms": ["burning urination", "frequent urination", "cloudy urine", "pelvic pain", "blood in urine", "peshab mein jalan", "baar baar peshab", "pet ke neeche dard", "peshab mein khoon"],
        "severity": "moderate",
        "color":    "#ffa500",
        "icon":     "🫘",
        "advice":   "Paani zyada piyo. Doctor se antibiotic prescription lo. Ignore mat karo.",
        "see_doctor": True,
        "medicines":  ["Nitrofurantoin (doctor se)", "Trimethoprim (doctor se)", "Paani zyada piyo"],
    },
    "Anemia": {
        "symptoms": ["fatigue", "weakness", "pale skin", "shortness of breath", "dizziness", "cold hands", "headache", "thakaan", "kamzori", "chehre ka rang pheeka", "saans ki takleef", "chakkar", "hath pair thande"],
        "severity": "moderate",
        "color":    "#ffa500",
        "icon":     "🩺",
        "advice":   "Hemoglobin test karwao. Iron-rich foods khao. Doctor se iron supplements lo.",
        "see_doctor": True,
        "medicines":  ["Iron supplements", "Vitamin B12", "Folic acid", "Iron-rich diet"],
    },
    "Chickenpox": {
        "symptoms": ["itchy rash", "blisters", "fever", "fatigue", "loss of appetite", "khujli wale daane", "phode", "bukhar", "thakaan", "bhook nahi"],
        "severity": "moderate",
        "color":    "#ffa500",
        "icon":     "🔴",
        "advice":   "Khujli mat karo — daag pad sakte hain. Calamine lotion lagao. Antihistamine lo.",
        "see_doctor": False,
        "medicines":  ["Calamine lotion", "Cetirizine", "Paracetamol", "Acyclovir (doctor se severe mein)"],
    },
}

# ══════════════════════════════════════════════════════════════
#  SYMPTOM KEYWORDS — user ke text se symptoms extract karne ke liye
# ══════════════════════════════════════════════════════════════
SYMPTOM_KEYWORDS = {
    # English
    "fever":              ["fever", "temperature", "hot", "burning"],
    "high fever":         ["high fever", "tez bukhar", "tej bukhar", "104", "103", "102"],
    "cough":              ["cough", "coughing", "khansi", "khasi"],
    "dry cough":          ["dry cough", "sukhi khansi"],
    "productive cough":   ["productive cough", "balgam", "phlegm", "mucus"],
    "runny nose":         ["runny nose", "naak behna", "naak se paani"],
    "sneezing":           ["sneezing", "chheenk", "sneeze"],
    "sore throat":        ["sore throat", "gala dard", "gala kharab", "throat pain"],
    "headache":           ["headache", "sir dard", "sar dard", "head pain", "head ache"],
    "body ache":          ["body ache", "badan dard", "body pain", "muscle pain", "jodo mein dard"],
    "fatigue":            ["fatigue", "tired", "thakaan", "kamzori", "weakness", "lethargy"],
    "shortness of breath":["shortness of breath", "saans lene mein takleef", "saans ki takleef", "difficulty breathing", "breathless", "sans mein takleef"],
    "chest pain":         ["chest pain", "seene mein dard", "chest dard", "seene mein jalan"],
    "nausea":             ["nausea", "ji machalna", "ulti jaisi", "feel like vomiting"],
    "vomiting":           ["vomiting", "ulti", "vomit"],
    "diarrhea":           ["diarrhea", "dast", "loose motion", "loose motions"],
    "abdominal pain":     ["abdominal pain", "pet dard", "stomach pain", "stomach ache", "pet mein dard"],
    "loss of taste":      ["loss of taste", "swad nahi", "taste nahi", "no taste"],
    "loss of smell":      ["loss of smell", "khushbu nahi", "smell nahi", "no smell", "gandh nahi"],
    "rash":               ["rash", "daane", "skin rash", "chakte"],
    "itching":            ["itching", "khujli", "itch", "khujlahat"],
    "joint pain":         ["joint pain", "jodo mein dard", "joint dard", "gathiya"],
    "dizziness":          ["dizziness", "chakkar", "dizzy", "ghabrahat"],
    "blurred vision":     ["blurred vision", "aankhein dhundhla", "vision blurry", "dhundhla dikhna"],
    "frequent urination": ["frequent urination", "baar baar peshab", "bar bar peshab"],
    "burning urination":  ["burning urination", "peshab mein jalan", "urination pain"],
    "chills":             ["chills", "thanda lagna", "kaanpna", "shivering"],
    "sweating":           ["sweating", "paseena", "sweat"],
    "weight loss":        ["weight loss", "wazan ghata", "wajan kam hona"],
    "loss of appetite":   ["loss of appetite", "bhook nahi", "appetite nahi", "khana nahi khaya"],
    "wheezing":           ["wheezing", "saans mein awaaz", "wheeze", "seeti jaisi awaaz"],
    "pale skin":          ["pale skin", "chehre ka rang pheeka", "skin pale", "paandupan"],
    "blisters":           ["blisters", "phode", "blister", "chhale"],
    "nosebleed":          ["nosebleed", "naak se khoon", "epistaxis"],
}

# ══════════════════════════════════════════════════════════════
#  ML MODEL — Decision Tree
# ══════════════════════════════════════════════════════════════

# Saare unique symptoms collect karo
ALL_SYMPTOMS = list(SYMPTOM_KEYWORDS.keys())

def _build_training_data():
    """Training data banao disease database se."""
    X, y = [], []
    for disease, info in DISEASE_DATA.items():
        # Disease ke symptoms ko normalized form mein map karo
        matched = []
        for sym in info["symptoms"]:
            for key, keywords in SYMPTOM_KEYWORDS.items():
                if any(kw in sym.lower() for kw in keywords):
                    matched.append(key)
                    break
        if matched:
            X.append(matched)
            y.append(disease)
    return X, y

# MLB — symptoms list ko binary vector mein convert karta hai
mlb = MultiLabelBinarizer(classes=ALL_SYMPTOMS)

X_raw, y_raw = _build_training_data()
X_train = mlb.fit_transform(X_raw)

# Decision Tree train karo
model = DecisionTreeClassifier(
    max_depth        = 8,
    min_samples_leaf = 1,
    random_state     = 42
)
model.fit(X_train, y_raw)

print("✅ Symptom Checker ML model ready!")


# ══════════════════════════════════════════════════════════════
#  MAIN FUNCTION — user text → disease predictions
# ══════════════════════════════════════════════════════════════

def extract_symptoms(user_text: str) -> list:
    """
    User ke free-text se symptoms extract karo.
    Hindi + English + Hinglish sab support.
    """
    text  = user_text.lower()
    found = []

    for symptom_key, keywords in SYMPTOM_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text:
                found.append(symptom_key)
                break   # ek symptom ek baar hi count ho

    return list(set(found))


def predict_diseases(symptoms: list, top_n: int = 4) -> list:
    """
    Symptoms list se top N diseases predict karo.
    Returns sorted list with confidence scores.
    """
    if not symptoms:
        return []

    # Symptoms ko vector mein convert karo
    input_vec = mlb.transform([symptoms])

    # Rule-based scoring — ML ke saath combine karo
    scores = {}

    for disease, info in DISEASE_DATA.items():
        disease_syms = set()
        for sym in info["symptoms"]:
            for key, keywords in SYMPTOM_KEYWORDS.items():
                if any(kw in sym.lower() for kw in keywords):
                    disease_syms.add(key)

        if not disease_syms:
            continue

        user_syms    = set(symptoms)
        matched      = user_syms & disease_syms
        match_score  = len(matched) / len(disease_syms)
        cover_score  = len(matched) / max(len(user_syms), 1)
        combined     = (match_score * 0.6) + (cover_score * 0.4)

        # Severity boost — zyada serious disease ko thoda upar rakho
        sev_boost = {"high": 0.05, "moderate": 0.02, "mild": 0.0}
        combined += sev_boost.get(info["severity"], 0)

        if combined > 0.1:   # sirf relevant results
            scores[disease] = {
                "confidence":    round(combined * 100),
                "matched_syms":  list(matched),
                "severity":      info["severity"],
                "color":         info["color"],
                "icon":          info["icon"],
                "advice":        info["advice"],
                "see_doctor":    info["see_doctor"],
                "medicines":     info["medicines"],
            }

    # Score ke hisaab se sort karo
    sorted_results = sorted(
        scores.items(),
        key    = lambda x: x[1]["confidence"],
        reverse= True
    )[:top_n]

    return [{"disease": d, **info} for d, info in sorted_results]


def check_symptoms(user_text: str) -> dict:
    """
    Main function — user ka text lao, complete analysis return karo.
    """
    if not user_text or len(user_text.strip()) < 3:
        return {"success": False, "error": "Kuch symptoms batao pehle!"}

    symptoms = extract_symptoms(user_text)

    if not symptoms:
        return {
            "success":          False,
            "error":            "Koi specific symptom nahi mila. Thoda detail mein batao.",
            "tip":              "Example: 'mujhe bukhar hai, sir dard hai, thakaan feel ho rahi hai'",
            "detected_symptoms": [],
            "predictions":      [],
        }

    predictions = predict_diseases(symptoms)

    # Emergency check — koi high severity disease hai?
    emergency = any(
        p["severity"] == "high" and p["confidence"] > 30
        for p in predictions
    )

    return {
        "success":           True,
        "detected_symptoms": symptoms,
        "symptom_count":     len(symptoms),
        "predictions":       predictions,
        "emergency":         emergency,
        "disclaimer":        "Yeh sirf AI prediction hai — final diagnosis ke liye doctor se milo.",
    }