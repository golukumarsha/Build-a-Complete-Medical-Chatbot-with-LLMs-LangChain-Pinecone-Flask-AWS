# src/drug_interaction.py — Drug Interaction Checker
"""
Drug Interaction Check karta hai using:
  1. RxNorm API  — medicine ka RxCUI (standard ID) fetch karta hai
  2. OpenFDA API — drug label mein interaction warnings dhundhta hai
  3. Local DB     — common Indian medicines ki known interactions

Flow:
  Drug A name → RxNorm → RxCUI
  Drug B name → RxNorm → RxCUI
  OpenFDA label search → interaction text extract
  Local known pairs → instant check
"""

import re
import urllib.request
import urllib.parse
import json
import time

# ══════════════════════════════════════════════════════════════════
#  LOCAL KNOWN INTERACTIONS DATABASE
#  (Common Indian medicines — offline fallback + instant results)
# ══════════════════════════════════════════════════════════════════

KNOWN_INTERACTIONS = [
    # ── Anticoagulants ────────────────────────────────────────────
    {
        "drugs":    ["warfarin", "aspirin"],
        "severity": "major",
        "effect":   "Dono saath lene se bleeding risk bahut badh jaati hai. Stomach ya brain mein internal bleeding ho sakti hai.",
        "advice":   "Avoid karo. Agar zaroori ho to doctor ki strict supervision mein lo. PT/INR regularly monitor karo.",
        "mechanism": "Aspirin platelet aggregation rokta hai + warfarin ka anticoagulant effect badhata hai."
    },
    {
        "drugs":    ["warfarin", "ibuprofen"],
        "severity": "major",
        "effect":   "Bleeding risk dramatically increase hoti hai. GI bleeding common side effect hai.",
        "advice":   "Ibuprofen ki jagah Paracetamol use karo. Doctor se alternative poochho.",
        "mechanism": "NSAIDs warfarin ko plasma proteins se displace karte hain — free warfarin level badhta hai."
    },
    {
        "drugs":    ["warfarin", "metronidazole"],
        "severity": "major",
        "effect":   "Warfarin ka effect 2-3 guna badh jaata hai. Severe bleeding risk.",
        "advice":   "Agar antibiotic zaroori ho to INR daily monitor karo. Warfarin dose adjust karni padegi.",
        "mechanism": "Metronidazole warfarin ke metabolism ko inhibit karta hai (CYP2C9 inhibition)."
    },

    # ── NSAIDs combinations ───────────────────────────────────────
    {
        "drugs":    ["ibuprofen", "aspirin"],
        "severity": "moderate",
        "effect":   "Aspirin ka cardioprotective effect reduce ho jaata hai. GI bleeding risk badh jaati hai.",
        "advice":   "Saath mat lo. Aspirin pehle lo (30 min), phir ibuprofen lo — ya doctor se poochho.",
        "mechanism": "Ibuprofen aspirin ke COX-1 binding ko block karta hai."
    },
    {
        "drugs":    ["ibuprofen", "naproxen"],
        "severity": "moderate",
        "effect":   "Do NSAIDs saath — gastric ulcer aur kidney damage ka risk bahut badh jaata hai.",
        "advice":   "Dono NSAIDs ek saath kabhi mat lo. Ek choose karo.",
        "mechanism": "Additive COX inhibition — stomach lining damage aur renal blood flow reduce hota hai."
    },
    {
        "drugs":    ["ibuprofen", "diclofenac"],
        "severity": "moderate",
        "effect":   "Double NSAID load — stomach ulcer, kidney failure, cardiovascular risk increase.",
        "advice":   "Dono ek saath mat lo. Sirf ek NSAID use karo at a time.",
        "mechanism": "Additive gastrointestinal aur renal toxicity."
    },

    # ── ACE Inhibitors / BP meds ──────────────────────────────────
    {
        "drugs":    ["lisinopril", "ibuprofen"],
        "severity": "moderate",
        "effect":   "Ibuprofen BP medicine ka effect kam kar deta hai. Kidney function deteriorate ho sakti hai.",
        "advice":   "Fever/pain ke liye Paracetamol use karo NSAIDs ki jagah.",
        "mechanism": "NSAIDs renal prostaglandins inhibit karte hain — ACE inhibitor ki efficacy ghatti hai."
    },
    {
        "drugs":    ["amlodipine", "simvastatin"],
        "severity": "moderate",
        "effect":   "Simvastatin ka blood level 77% tak badh sakta hai — myopathy aur rhabdomyolysis risk.",
        "advice":   "Simvastatin dose 20mg se zyada mat do jab amlodipine chal rahi ho. Doctor se consult karo.",
        "mechanism": "Amlodipine CYP3A4 inhibit karta hai — simvastatin ka metabolism slow hota hai."
    },
    {
        "drugs":    ["enalapril", "potassium"],
        "severity": "moderate",
        "effect":   "Hyperkalemia (dangerously high potassium) ho sakti hai — heart arrhythmia risk.",
        "advice":   "Potassium supplements + ACE inhibitor = dangerous. Doctor se monitor karwao.",
        "mechanism": "ACE inhibitors potassium retention badhate hain."
    },

    # ── Antibiotics ───────────────────────────────────────────────
    {
        "drugs":    ["metformin", "alcohol"],
        "severity": "major",
        "effect":   "Lactic acidosis ka serious risk — life threatening ho sakta hai.",
        "advice":   "Metformin ke saath alcohol bilkul mat lo.",
        "mechanism": "Alcohol aur metformin dono lactic acid production badhate hain."
    },
    {
        "drugs":    ["ciprofloxacin", "antacid"],
        "severity": "moderate",
        "effect":   "Antacid ciprofloxacin ka absorption 50-90% tak kam kar deta hai — antibiotic kaam nahi karta.",
        "advice":   "Ciprofloxacin 2 ghante pehle ya 6 ghante baad lo antacid se.",
        "mechanism": "Antacid ke minerals (Mg, Al, Ca) ciprofloxacin ke saath chelate form karte hain."
    },
    {
        "drugs":    ["azithromycin", "antacid"],
        "severity": "minor",
        "effect":   "Absorption thoda kam ho sakta hai. Overall effect minor hai.",
        "advice":   "1-2 ghante ka gap rakhna behtar hai.",
        "mechanism": "Antacid gastric pH change karta hai — absorption affect hoti hai."
    },
    {
        "drugs":    ["amoxicillin", "warfarin"],
        "severity": "moderate",
        "effect":   "Antibiotic gut bacteria destroy karta hai — Vitamin K production ghatti hai — warfarin effect badh jaata hai.",
        "advice":   "Antibiotic course ke dauran aur baad mein INR monitor karo.",
        "mechanism": "Gut flora destruction → Vitamin K synthesis reduced → enhanced anticoagulation."
    },

    # ── Diabetes medicines ────────────────────────────────────────
    {
        "drugs":    ["metformin", "ibuprofen"],
        "severity": "moderate",
        "effect":   "Kidney par double stress — metformin accumulate ho sakta hai — lactic acidosis risk badh jaata hai.",
        "advice":   "Paracetamol ko prefer karo. Kidney function monitor karo.",
        "mechanism": "NSAIDs renal blood flow reduce karte hain — metformin clearance ghatti hai."
    },
    {
        "drugs":    ["glipizide", "fluconazole"],
        "severity": "major",
        "effect":   "Blood sugar bahut zyada gir sakti hai (severe hypoglycemia) — coma ka risk.",
        "advice":   "Ye combination avoid karo. Doctor se alternative antifungal poochho.",
        "mechanism": "Fluconazole CYP2C9 inhibit karta hai — glipizide ka metabolism slow hota hai."
    },
    {
        "drugs":    ["metformin", "contrast dye"],
        "severity": "major",
        "effect":   "CT scan/X-ray contrast + metformin = kidney failure aur lactic acidosis ka serious risk.",
        "advice":   "Scan se 48 ghante pehle metformin band karo. Doctor ko batao.",
        "mechanism": "Contrast dye transiently kidney function reduce karta hai."
    },

    # ── Cardiac medicines ─────────────────────────────────────────
    {
        "drugs":    ["digoxin", "amiodarone"],
        "severity": "major",
        "effect":   "Digoxin toxicity — nausea, vomiting, dangerous heart rhythms (bradycardia, AV block).",
        "advice":   "Digoxin dose 50% reduce karo. Daily ECG monitoring zaroori hai.",
        "mechanism": "Amiodarone P-glycoprotein inhibit karta hai — digoxin level badh jaata hai."
    },
    {
        "drugs":    ["atenolol", "verapamil"],
        "severity": "major",
        "effect":   "Severe bradycardia (heart rate bahut kam), heart block, cardiac arrest possible.",
        "advice":   "Ye combination doctors avoid karte hain. Ek hi lena chahiye.",
        "mechanism": "Dono drugs cardiac conduction slow karte hain — additive effect dangerous hai."
    },

    # ── Mental health ─────────────────────────────────────────────
    {
        "drugs":    ["tramadol", "ssri"],
        "severity": "major",
        "effect":   "Serotonin Syndrome — agitation, confusion, rapid heart rate, high fever — medical emergency.",
        "advice":   "Ye combination avoid karo. Doctor se non-serotonergic alternative poochho.",
        "mechanism": "Dono drugs serotonin level badhate hain — toxic serotonin syndrome hota hai."
    },
    {
        "drugs":    ["fluoxetine", "tramadol"],
        "severity": "major",
        "effect":   "Serotonin syndrome + tramadol ka seizure risk badh jaata hai.",
        "advice":   "Avoid. Agar pain management zaroori ho to doctor se non-opioid alternative lo.",
        "mechanism": "CYP2D6 inhibition + dual serotonergic mechanism."
    },
    {
        "drugs":    ["alprazolam", "alcohol"],
        "severity": "major",
        "effect":   "CNS depression — extreme drowsiness, respiratory failure, coma, death possible.",
        "advice":   "Absolutely avoid. Dono saath lena life-threatening hai.",
        "mechanism": "Additive CNS depression — GABA receptor enhanced effect."
    },

    # ── Statins ───────────────────────────────────────────────────
    {
        "drugs":    ["atorvastatin", "clarithromycin"],
        "severity": "major",
        "effect":   "Statin level 10x tak badh sakta hai — severe muscle damage (rhabdomyolysis), kidney failure.",
        "advice":   "Clarithromycin ke dauran atorvastatin temporarily band karo.",
        "mechanism": "Clarithromycin strong CYP3A4 inhibitor hai — statin metabolism completely block hoti hai."
    },
    {
        "drugs":    ["rosuvastatin", "gemfibrozil"],
        "severity": "major",
        "effect":   "Myopathy aur rhabdomyolysis ka high risk — muscle breakdown → kidney failure.",
        "advice":   "Ye combination avoid karo. Fenofibrate safer alternative hai.",
        "mechanism": "Gemfibrozil statin uptake transporter inhibit karta hai."
    },

    # ── Common OTC ────────────────────────────────────────────────
    {
        "drugs":    ["paracetamol", "alcohol"],
        "severity": "major",
        "effect":   "Liver damage ka serious risk. Chronic alcohol use + paracetamol = liver failure.",
        "advice":   "Regular alcohol peene walon ko paracetamol avoid karna chahiye ya dose kam rakhna chahiye.",
        "mechanism": "Alcohol CYP2E1 induce karta hai — toxic metabolite NAPQI zyada banta hai."
    },
    {
        "drugs":    ["paracetamol", "warfarin"],
        "severity": "moderate",
        "effect":   "Regular high-dose paracetamol warfarin ka effect badha sakti hai — bleeding risk.",
        "advice":   "Occasional low dose (500mg) safe hai. Regular high dose avoid karo.",
        "mechanism": "Paracetamol Vitamin K metabolism interfere karta hai at high doses."
    },
    {
        "drugs":    ["cetirizine", "alcohol"],
        "severity": "moderate",
        "effect":   "Extreme drowsiness aur CNS depression. Driving/machinery operate mat karo.",
        "advice":   "Cetirizine ke saath alcohol avoid karo.",
        "mechanism": "Additive CNS sedation."
    },
    {
        "drugs":    ["omeprazole", "clopidogrel"],
        "severity": "moderate",
        "effect":   "Clopidogrel ka antiplatelet effect 40-50% kam ho jaata hai — heart attack ka risk badh sakta hai.",
        "advice":   "PPI ki jagah pantoprazole use karo — yeh less interaction karta hai.",
        "mechanism": "Omeprazole CYP2C19 inhibit karta hai — clopidogrel active form mein convert nahi hota."
    },

    # ── Antibiotics + OCP ─────────────────────────────────────────
    {
        "drugs":    ["rifampicin", "contraceptive"],
        "severity": "major",
        "effect":   "Oral contraceptive pill fail ho sakti hai — unwanted pregnancy ka risk.",
        "advice":   "Rifampicin ke dauran aur 4 weeks baad tak additional contraception use karo.",
        "mechanism": "Rifampicin strong enzyme inducer — contraceptive hormone metabolism bahut fast ho jaata hai."
    },

    # ── Supplements ───────────────────────────────────────────────
    {
        "drugs":    ["st. john's wort", "antidepressant"],
        "severity": "major",
        "effect":   "Serotonin syndrome ka risk — herbal supplement dangerous ho sakta hai.",
        "advice":   "Doctor ko batao agar koi herbal supplement le rahe ho.",
        "mechanism": "St. John's Wort serotonin reuptake inhibit karta hai."
    },
    {
        "drugs":    ["calcium", "iron"],
        "severity": "minor",
        "effect":   "Calcium iron ka absorption 50% tak reduce kar sakta hai.",
        "advice":   "Dono alag alag time pe lo — 2 ghante ka gap rakhna chahiye.",
        "mechanism": "Calcium iron ke absorption sites pe compete karta hai."
    },
    {
        "drugs":    ["zinc", "iron"],
        "severity": "minor",
        "effect":   "High dose mein dono ek dusre ka absorption reduce karte hain.",
        "advice":   "Alag time pe lo. Meals ke saath lena better hai.",
        "mechanism": "Divalent cation competition for intestinal absorption."
    },
]


# ══════════════════════════════════════════════════════════════════
#  HELPER — HTTP GET (no external libraries)
# ══════════════════════════════════════════════════════════════════

def _http_get(url: str, timeout: int = 6) -> dict | None:
    """Simple HTTP GET — returns parsed JSON or None."""
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "MediBot/1.0 (medical-chatbot; educational use)"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[DrugAPI] HTTP error for {url[:60]}: {e}")
        return None


# ══════════════════════════════════════════════════════════════════
#  STEP 1: RxNorm — drug name → RxCUI
# ══════════════════════════════════════════════════════════════════

def get_rxcui(drug_name: str) -> str | None:
    """
    RxNorm API se drug ka standard ID (RxCUI) fetch karo.
    Example: "paracetamol" → "161"
    """
    name = drug_name.strip().lower()
    # Common aliases handle karo
    aliases = {
        "paracetamol": "acetaminophen",
        "tylenol":     "acetaminophen",
        "crocin":      "acetaminophen",
        "dolo":        "acetaminophen",
        "brufen":      "ibuprofen",
        "combiflam":   "ibuprofen",
        "ecosprin":    "aspirin",
        "disprin":     "aspirin",
        "glucophage":  "metformin",
        "glycomet":    "metformin",
        "pantop":      "pantoprazole",
        "pan":         "pantoprazole",
        "rantac":      "ranitidine",
        "allegra":     "fexofenadine",
        "cetrizine":   "cetirizine",
        "cetzine":     "cetirizine",
    }
    search_name = aliases.get(name, name)

    url = f"https://rxnav.nlm.nih.gov/REST/rxcui.json?name={urllib.parse.quote(search_name)}&search=2"
    data = _http_get(url)
    if data:
        try:
            rxcui = data["idGroup"]["rxnormId"][0]
            return rxcui
        except (KeyError, IndexError, TypeError):
            pass

    # Approximate search try karo
    url2 = f"https://rxnav.nlm.nih.gov/REST/approximateTerm.json?term={urllib.parse.quote(search_name)}&maxEntries=1"
    data2 = _http_get(url2)
    if data2:
        try:
            return data2["approximateGroup"]["candidate"][0]["rxcui"]
        except (KeyError, IndexError, TypeError):
            pass
    return None


# ══════════════════════════════════════════════════════════════════
#  STEP 2: OpenFDA — drug label mein interactions dhundho
# ══════════════════════════════════════════════════════════════════

def search_openfda_interactions(drug_a: str, drug_b: str) -> list[str]:
    """
    OpenFDA drug label API se interaction warnings extract karo.
    Drug A ki label mein Drug B ka mention dhundho.
    """
    warnings = []

    def fetch_label_warnings(primary: str, secondary: str) -> list[str]:
        found = []
        url = (
            f"https://api.fda.gov/drug/label.json?"
            f"search=openfda.brand_name:\"{urllib.parse.quote(primary)}\""
            f"+AND+drug_interactions:\"{urllib.parse.quote(secondary)}\""
            f"&limit=1"
        )
        data = _http_get(url)
        if data and "results" in data:
            for result in data["results"]:
                interactions = result.get("drug_interactions", [])
                for text in interactions:
                    # Secondary drug ka mention dhundho
                    if secondary.lower() in text.lower():
                        # Relevant sentence extract karo
                        sentences = re.split(r'(?<=[.!?])\s+', text)
                        for sent in sentences:
                            if secondary.lower() in sent.lower() and len(sent) > 20:
                                clean = re.sub(r'\s+', ' ', sent.strip())
                                if len(clean) < 400:
                                    found.append(clean)
        return found[:2]  # Max 2 warnings per direction

    # Dono directions check karo
    warnings.extend(fetch_label_warnings(drug_a, drug_b))
    warnings.extend(fetch_label_warnings(drug_b, drug_a))

    # Generic name se bhi try karo
    if len(warnings) == 0:
        url_generic = (
            f"https://api.fda.gov/drug/label.json?"
            f"search=drug_interactions:\"{urllib.parse.quote(drug_a)}\""
            f"+AND+drug_interactions:\"{urllib.parse.quote(drug_b)}\""
            f"&limit=1"
        )
        data = _http_get(url_generic)
        if data and "results" in data:
            for result in data["results"]:
                for text in result.get("drug_interactions", []):
                    if drug_a.lower() in text.lower() and drug_b.lower() in text.lower():
                        sentences = re.split(r'(?<=[.!?])\s+', text)
                        for sent in sentences:
                            if (drug_a.lower() in sent.lower() or drug_b.lower() in sent.lower()):
                                clean = re.sub(r'\s+', ' ', sent.strip())
                                if 20 < len(clean) < 400:
                                    warnings.append(clean)
                                    if len(warnings) >= 3:
                                        return warnings

    return list(set(warnings))[:4]


# ══════════════════════════════════════════════════════════════════
#  STEP 3: RxNorm Interaction API
# ══════════════════════════════════════════════════════════════════

def check_rxnorm_interaction(rxcui_a: str, rxcui_b: str) -> dict | None:
    """
    RxNorm Interaction API se direct interaction check karo.
    Returns interaction info ya None.
    """
    if not rxcui_a or not rxcui_b:
        return None

    url = f"https://rxnav.nlm.nih.gov/REST/interaction/interaction.json?rxcui={rxcui_a}"
    data = _http_get(url)
    if not data:
        return None

    try:
        groups = data.get("interactionTypeGroup", [])
        for group in groups:
            for itype in group.get("interactionType", []):
                for pair in itype.get("interactionPair", []):
                    concepts = pair.get("interactionConcept", [])
                    rxcuis_in_pair = [c.get("minConceptItem", {}).get(
                        "rxcui") for c in concepts]
                    if rxcui_b in rxcuis_in_pair:
                        return {
                            "description": pair.get("description", ""),
                            "severity":    pair.get("severity", "").lower(),
                            "source":      group.get("sourceDisclaimer", "RxNorm")
                        }
    except Exception as e:
        print(f"[RxNorm interaction parse error]: {e}")
    return None


# ══════════════════════════════════════════════════════════════════
#  STEP 4: LOCAL DB Check
# ══════════════════════════════════════════════════════════════════

def check_local_interactions(drug_a: str, drug_b: str) -> dict | None:
    """
    Local database mein known interaction dhundho.
    Fuzzy match — partial names bhi match ho jaate hain.
    """
    a = drug_a.lower().strip()
    b = drug_b.lower().strip()

    for entry in KNOWN_INTERACTIONS:
        drugs = [d.lower() for d in entry["drugs"]]
        # Direct match ya partial match
        match_a = any(d in a or a in d for d in drugs)
        match_b = any(d in b or b in d for d in drugs)
        if match_a and match_b and a != b:
            # Ensure different drugs matched different entries
            a_drug = next((d for d in drugs if d in a or a in d), None)
            b_drug = next((d for d in drugs if d in b or b in d), None)
            if a_drug and b_drug and a_drug != b_drug:
                return entry
    return None


# ══════════════════════════════════════════════════════════════════
#  MAIN FUNCTION — Complete interaction check
# ══════════════════════════════════════════════════════════════════

def check_drug_interaction(drug_a: str, drug_b: str) -> dict:
    """
    Main function — do medicines ka interaction check karo.

    Returns:
    {
        "success": True/False,
        "drug_a": "...", "drug_b": "...",
        "interaction_found": True/False,
        "severity": "major"/"moderate"/"minor"/"none",
        "severity_color": "#...",
        "local_result": {...} or None,
        "rxnorm_result": {...} or None,
        "fda_warnings": [...],
        "rxcui_a": "...", "rxcui_b": "...",
        "summary": "...",
        "advice": "...",
        "sources": [...],
        "disclaimer": "..."
    }
    """
    drug_a = drug_a.strip()
    drug_b = drug_b.strip()

    if not drug_a or not drug_b:
        return {"success": False, "error": "Dono medicines ka naam daalo"}

    if drug_a.lower() == drug_b.lower():
        return {"success": False, "error": "Dono alag medicines daalo"}

    result = {
        "success":          True,
        "drug_a":           drug_a,
        "drug_b":           drug_b,
        "interaction_found": False,
        "severity":         "none",
        "severity_color":   "#00c896",
        "local_result":     None,
        "rxnorm_result":    None,
        "fda_warnings":     [],
        "rxcui_a":          None,
        "rxcui_b":          None,
        "summary":          "",
        "advice":           "",
        "mechanism":        "",
        "sources":          [],
        "disclaimer":       "Yeh sirf AI-based information hai. Koi bhi medicine lene se pehle doctor ya pharmacist se zaroor poochhen."
    }

    # ── 1. Local DB check (fastest) ──────────────────────────────
    local = check_local_interactions(drug_a, drug_b)
    if local:
        result["local_result"] = local
        result["interaction_found"] = True
        result["severity"] = local["severity"]
        result["summary"] = local["effect"]
        result["advice"] = local["advice"]
        result["mechanism"] = local.get("mechanism", "")
        result["sources"].append("MediBot Local Database")

    # ── 2. RxNorm CUI fetch ──────────────────────────────────────
    rxcui_a = get_rxcui(drug_a)
    rxcui_b = get_rxcui(drug_b)
    result["rxcui_a"] = rxcui_a
    result["rxcui_b"] = rxcui_b

    # ── 3. RxNorm Interaction API ────────────────────────────────
    if rxcui_a and rxcui_b:
        rx_interaction = check_rxnorm_interaction(rxcui_a, rxcui_b)
        if not rx_interaction:
            # Reverse bhi try karo
            rx_interaction = check_rxnorm_interaction(rxcui_b, rxcui_a)

        if rx_interaction and rx_interaction.get("description"):
            result["rxnorm_result"] = rx_interaction
            result["interaction_found"] = True
            result["sources"].append("RxNorm (NLM)")

            # Agar local result nahi mila to RxNorm use karo
            if not result["summary"]:
                result["summary"] = rx_interaction["description"]

            # Severity upgrade agar RxNorm zyada serious bata raha hai
            sev_order = {"none": 0, "minor": 1, "moderate": 2, "major": 3}
            rx_sev = rx_interaction.get("severity", "moderate").lower()
            if rx_sev in sev_order and sev_order.get(rx_sev, 0) > sev_order.get(result["severity"], 0):
                result["severity"] = rx_sev

    # ── 4. OpenFDA Label search ──────────────────────────────────
    fda_warnings = search_openfda_interactions(drug_a, drug_b)
    if fda_warnings:
        result["fda_warnings"] = fda_warnings
        result["interaction_found"] = True
        result["sources"].append("OpenFDA Drug Labels")
        if not result["summary"] and fda_warnings:
            result["summary"] = fda_warnings[0]

    # ── 5. Severity color assign karo ────────────────────────────
    severity_config = {
        "major":    {"color": "#ff5c5c", "icon": "🚨", "label": "MAJOR — Avoid karo"},
        "moderate": {"color": "#ffa500", "icon": "⚠️",  "label": "MODERATE — Caution"},
        "minor":    {"color": "#3b9eff", "icon": "ℹ️",  "label": "MINOR — Monitor karo"},
        "none":     {"color": "#00c896", "icon": "✅",  "label": "No Interaction Found"},
    }
    sev = result["severity"] if result["severity"] in severity_config else "none"
    result["severity_color"] = severity_config[sev]["color"]
    result["severity_icon"] = severity_config[sev]["icon"]
    result["severity_label"] = severity_config[sev]["label"]

    # ── 6. Default advice agar kuch nahi mila ───────────────────
    if not result["interaction_found"]:
        result["summary"] = f"{drug_a} aur {drug_b} ke beech koi known major interaction nahi mila."
        result["advice"] = "Hamare database mein is combination ka record nahi hai. Iska matlab yeh nahi ki yeh bilkul safe hai. Doctor ya pharmacist se confirm karo."
    elif not result["advice"]:
        if sev == "major":
            result["advice"] = "⚠️ Yeh combination dangerous ho sakta hai. Turant apne doctor se baat karo."
        elif sev == "moderate":
            result["advice"] = "Caution rakhein. Doctor ki supervision mein lo. Koi bhi side effect ho to immediately batao."
        else:
            result["advice"] = "Minor interaction hai. Normal use mein mostly safe hai lekin doctor ko inform karo."

    result["sources"] = list(set(result["sources"])) if result["sources"] else [
        "No external source"]
    return result
