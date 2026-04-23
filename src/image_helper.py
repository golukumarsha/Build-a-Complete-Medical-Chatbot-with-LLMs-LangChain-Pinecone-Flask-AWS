"""
src/image_helper.py  — v3 RELIABLE VERSION
Wikipedia pe depend nahi karta — network issues se safe.
Unsplash ke free public image URLs use karta hai — hamesha kaam karta hai.
Koi API key nahi chahiye. No external requests at runtime.
"""

# ─────────────────────────────────────────────────────────────────────────────
# Har entry:  "keyword" → { display_name, image_url, description, wiki_url }
# image_url = Unsplash direct CDN link, always loads, no auth needed
# ─────────────────────────────────────────────────────────────────────────────

MEDICAL_DATA = {

    # ── Diseases / Conditions ─────────────────────────────────────────────────
    "diabetes": {
        "display_name": "Diabetes",
        "image_url":    "https://images.unsplash.com/photo-1593491205049-7f032d28cf01?w=400&q=80",
        "description":  "Diabetes ek chronic condition hai jisme blood sugar level high rehta hai. Type 1, Type 2 aur gestational diabetes hote hain.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Diabetes",
    },
    "diabetic": {
        "display_name": "Diabetes",
        "image_url":    "https://images.unsplash.com/photo-1593491205049-7f032d28cf01?w=400&q=80",
        "description":  "Diabetes ek chronic condition hai jisme blood sugar level high rehta hai.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Diabetes",
    },
    "heart attack": {
        "display_name": "Heart Attack",
        "image_url":    "https://images.unsplash.com/photo-1628348068343-c6a848d2b6dd?w=400&q=80",
        "description":  "Heart attack tab hota hai jab heart ko blood supply band ho jaati hai. Emergency treatment zaruri hai.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Myocardial_infarction",
    },
    "heart disease": {
        "display_name": "Heart Disease",
        "image_url":    "https://images.unsplash.com/photo-1628348068343-c6a848d2b6dd?w=400&q=80",
        "description":  "Cardiovascular disease heart aur blood vessels ko affect karta hai. Duniya mein death ki #1 wajah.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Cardiovascular_disease",
    },
    "heart": {
        "display_name": "Human Heart",
        "image_url":    "https://images.unsplash.com/photo-1628348068343-c6a848d2b6dd?w=400&q=80",
        "description":  "Heart ek muscular organ hai jo blood pump karta hai. Ek din mein ~100,000 baar dhakdhakta hai.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Heart",
    },
    "cardiac": {
        "display_name": "Cardiac (Heart)",
        "image_url":    "https://images.unsplash.com/photo-1628348068343-c6a848d2b6dd?w=400&q=80",
        "description":  "Cardiac problems heart se related hoti hain. Timely diagnosis bahut zaroori hai.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Heart",
    },
    "asthma": {
        "display_name": "Asthma",
        "image_url":    "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=400&q=80",
        "description":  "Asthma respiratory condition hai jisme airways narrow ho jaati hain. Inhaler se manage kiya jaata hai.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Asthma",
    },
    "cancer": {
        "display_name": "Cancer",
        "image_url":    "https://images.unsplash.com/photo-1576671081837-49000212a370?w=400&q=80",
        "description":  "Cancer mein cells uncontrolled grow karti hain. Early detection se treatment bahut better hota hai.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Cancer",
    },
    "tumor": {
        "display_name": "Tumor",
        "image_url":    "https://images.unsplash.com/photo-1576671081837-49000212a370?w=400&q=80",
        "description":  "Tumor cells ka abnormal mass hota hai. Benign (safe) ya malignant (cancerous) ho sakta hai.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Tumor",
    },
    "hypertension": {
        "display_name": "Hypertension (High BP)",
        "image_url":    "https://images.unsplash.com/photo-1559757175-0eb30cd8c063?w=400&q=80",
        "description":  "Hypertension mein blood pressure consistently high rehta hai. 'Silent killer' kehte hain.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Hypertension",
    },
    "blood pressure": {
        "display_name": "Blood Pressure",
        "image_url":    "https://images.unsplash.com/photo-1559757175-0eb30cd8c063?w=400&q=80",
        "description":  "Blood pressure arteries ki walls pe blood ki force hai. Normal: 120/80 mmHg.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Blood_pressure",
    },
    "stroke": {
        "display_name": "Stroke",
        "image_url":    "https://images.unsplash.com/photo-1530497610245-94d3c16cda28?w=400&q=80",
        "description":  "Stroke tab hota hai jab brain ki blood supply cut ho jaati hai. FAST method yaad rakho.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Stroke",
    },
    "pneumonia": {
        "display_name": "Pneumonia",
        "image_url":    "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=400&q=80",
        "description":  "Pneumonia lungs ki infection hai. Bacterial, viral ya fungal ho sakti hai.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Pneumonia",
    },
    "tuberculosis": {
        "display_name": "Tuberculosis (TB)",
        "image_url":    "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=400&q=80",
        "description":  "TB ek bacterial infection hai jo lungs ko affect karta hai. 6 mahine antibiotics se treatable.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Tuberculosis",
    },
    "malaria": {
        "display_name": "Malaria",
        "image_url":    "https://images.unsplash.com/photo-1585435557343-3b092031a831?w=400&q=80",
        "description":  "Malaria Plasmodium parasite se hota hai jo infected mosquito ke kaatne se failta hai.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Malaria",
    },
    "covid": {
        "display_name": "COVID-19",
        "image_url":    "https://images.unsplash.com/photo-1584483766114-2cea6facdf57?w=400&q=80",
        "description":  "COVID-19 SARS-CoV-2 virus se hoti hai. Fever, cough aur breathing problems common symptoms hain.",
        "wiki_url":     "https://en.wikipedia.org/wiki/COVID-19",
    },
    "alzheimer": {
        "display_name": "Alzheimer's Disease",
        "image_url":    "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=400&q=80",
        "description":  "Alzheimer's ek progressive brain disorder hai jo memory aur thinking ko affect karta hai.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Alzheimer%27s_disease",
    },
    "parkinson": {
        "display_name": "Parkinson's Disease",
        "image_url":    "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=400&q=80",
        "description":  "Parkinson's ek nervous system disorder hai. Tremors, stiffness aur slow movement hoti hai.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Parkinson%27s_disease",
    },
    "arthritis": {
        "display_name": "Arthritis",
        "image_url":    "https://images.unsplash.com/photo-1530497610245-94d3c16cda28?w=400&q=80",
        "description":  "Arthritis joints ki inflammation hai. Joint pain, swelling aur stiffness common symptoms hain.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Arthritis",
    },
    "depression": {
        "display_name": "Depression",
        "image_url":    "https://images.unsplash.com/photo-1493836512294-502baa1986e2?w=400&q=80",
        "description":  "Depression ek mental health condition hai. Sadness, hopelessness aur energy loss hoti hai.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Depression_(mood)",
    },
    "anxiety": {
        "display_name": "Anxiety Disorder",
        "image_url":    "https://images.unsplash.com/photo-1493836512294-502baa1986e2?w=400&q=80",
        "description":  "Anxiety disorder mein excessive worry aur fear hoti hai jo daily life affect karta hai.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Anxiety",
    },
    "fever": {
        "display_name": "Fever",
        "image_url":    "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=400&q=80",
        "description":  "Fever body temperature ka 37°C se zyada hona hai. Infection ke against body ka natural response.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Fever",
    },
    "infection": {
        "display_name": "Infection",
        "image_url":    "https://images.unsplash.com/photo-1585435557343-3b092031a831?w=400&q=80",
        "description":  "Infection harmful microorganisms ka body mein entry karna hai. Bacterial, viral ya fungal ho sakti hai.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Infection",
    },
    "fracture": {
        "display_name": "Bone Fracture",
        "image_url":    "https://images.unsplash.com/photo-1530497610245-94d3c16cda28?w=400&q=80",
        "description":  "Fracture bone ka toot jaana hai. X-ray se diagnose hota hai, plaster ya surgery se treat.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Bone_fracture",
    },
    "hiv": {
        "display_name": "HIV",
        "image_url":    "https://images.unsplash.com/photo-1585435557343-3b092031a831?w=400&q=80",
        "description":  "HIV immune system ko weaken karta hai. Antiretroviral therapy se long healthy life possible hai.",
        "wiki_url":     "https://en.wikipedia.org/wiki/HIV",
    },
    "cholesterol": {
        "display_name": "Cholesterol",
        "image_url":    "https://images.unsplash.com/photo-1628348068343-c6a848d2b6dd?w=400&q=80",
        "description":  "Cholesterol blood mein fatty substance hai. High LDL heart disease ka risk badhata hai.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Cholesterol",
    },
    "anemia": {
        "display_name": "Anemia",
        "image_url":    "https://images.unsplash.com/photo-1559757175-0eb30cd8c063?w=400&q=80",
        "description":  "Anemia mein red blood cells ya hemoglobin ki kami hoti hai. Fatigue aur weakness hoti hai.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Anemia",
    },
    "migraine": {
        "display_name": "Migraine",
        "image_url":    "https://images.unsplash.com/photo-1516302752625-fcc3c50ae61f?w=400&q=80",
        "description":  "Migraine intense headache hai jo nausea aur light sensitivity ke saath aata hai.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Migraine",
    },
    "headache": {
        "display_name": "Headache",
        "image_url":    "https://images.unsplash.com/photo-1516302752625-fcc3c50ae61f?w=400&q=80",
        "description":  "Headache head ya neck mein pain hai. Tension headache sabse common type hai.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Headache",
    },
    "epilepsy": {
        "display_name": "Epilepsy",
        "image_url":    "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=400&q=80",
        "description":  "Epilepsy neurological disorder hai jisme recurrent seizures aate hain.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Epilepsy",
    },
    "obesity": {
        "display_name": "Obesity",
        "image_url":    "https://images.unsplash.com/photo-1576671081837-49000212a370?w=400&q=80",
        "description":  "Obesity mein excess body fat hoti hai. BMI 30+ obesity consider kiya jaata hai.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Obesity",
    },
    "dengue": {
        "display_name": "Dengue Fever",
        "image_url":    "https://images.unsplash.com/photo-1585435557343-3b092031a831?w=400&q=80",
        "description":  "Dengue mosquito-borne viral infection hai. High fever, severe headache aur joint pain hota hai.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Dengue_fever",
    },
    "typhoid": {
        "display_name": "Typhoid Fever",
        "image_url":    "https://images.unsplash.com/photo-1585435557343-3b092031a831?w=400&q=80",
        "description":  "Typhoid Salmonella typhi bacteria se hota hai. Contaminated food/water se failta hai.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Typhoid_fever",
    },
    "allergy": {
        "display_name": "Allergy",
        "image_url":    "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=400&q=80",
        "description":  "Allergy tab hoti hai jab immune system kisi harmless substance ko threat samajhta hai.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Allergy",
    },
    "jaundice": {
        "display_name": "Jaundice",
        "image_url":    "https://images.unsplash.com/photo-1559757175-0eb30cd8c063?w=400&q=80",
        "description":  "Jaundice mein skin/eyes yellow ho jaate hain. Liver ya bile duct problem ka sign hai.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Jaundice",
    },
    "vomiting": {
        "display_name": "Vomiting",
        "image_url":    "https://images.unsplash.com/photo-1576671081837-49000212a370?w=400&q=80",
        "description":  "Vomiting stomach contents ka forceful expulsion hai. Infection, food poisoning ya motion sickness se hota hai.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Vomiting",
    },
    "diarrhea": {
        "display_name": "Diarrhea",
        "image_url":    "https://images.unsplash.com/photo-1576671081837-49000212a370?w=400&q=80",
        "description":  "Diarrhea mein loose, watery stools frequent hote hain. Dehydration se bachne ke liye ORS lena zaroori hai.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Diarrhea",
    },

    # ── Medicines ─────────────────────────────────────────────────────────────
    "paracetamol": {
        "display_name": "Paracetamol",
        "image_url":    "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=400&q=80",
        "description":  "Paracetamol common pain reliever aur fever reducer hai. Adult dose: 500mg-1g har 4-6 ghante.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Paracetamol",
    },
    "acetaminophen": {
        "display_name": "Acetaminophen (Paracetamol)",
        "image_url":    "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=400&q=80",
        "description":  "Acetaminophen pain aur fever ke liye widely used medicine hai.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Paracetamol",
    },
    "ibuprofen": {
        "display_name": "Ibuprofen",
        "image_url":    "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=400&q=80",
        "description":  "Ibuprofen NSAID hai jo pain, fever aur inflammation reduce karta hai. Khane ke saath lena chahiye.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Ibuprofen",
    },
    "aspirin": {
        "display_name": "Aspirin",
        "image_url":    "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=400&q=80",
        "description":  "Aspirin pain relief, fever aur blood thinning ke liye use hoti hai. Heart attack prevention mein bhi kaam aati.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Aspirin",
    },
    "amoxicillin": {
        "display_name": "Amoxicillin",
        "image_url":    "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=400&q=80",
        "description":  "Amoxicillin broad-spectrum antibiotic hai jo bacterial infections treat karta hai.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Amoxicillin",
    },
    "metformin": {
        "display_name": "Metformin",
        "image_url":    "https://images.unsplash.com/photo-1593491205049-7f032d28cf01?w=400&q=80",
        "description":  "Metformin Type 2 diabetes ki first-line treatment hai. Blood sugar control karta hai.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Metformin",
    },
    "insulin": {
        "display_name": "Insulin",
        "image_url":    "https://images.unsplash.com/photo-1593491205049-7f032d28cf01?w=400&q=80",
        "description":  "Insulin pancreas ka hormone hai jo blood sugar regulate karta hai. Diabetes mein inject kiya jaata hai.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Insulin",
    },
    "antibiotic": {
        "display_name": "Antibiotics",
        "image_url":    "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=400&q=80",
        "description":  "Antibiotics bacterial infections kill karte hain. Full course complete karna zaruri hai — resistance rokne ke liye.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Antibiotic",
    },
    "vaccine": {
        "display_name": "Vaccine",
        "image_url":    "https://images.unsplash.com/photo-1584483766114-2cea6facdf57?w=400&q=80",
        "description":  "Vaccine immune system ko disease se ladne ke liye prepare karti hai. Prevention ka sabse important tool.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Vaccine",
    },
    "penicillin": {
        "display_name": "Penicillin",
        "image_url":    "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=400&q=80",
        "description":  "Penicillin pehla antibiotic tha, 1928 mein discover hua. Aaj bhi bacterial infections mein use hota hai.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Penicillin",
    },
    "omeprazole": {
        "display_name": "Omeprazole",
        "image_url":    "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=400&q=80",
        "description":  "Omeprazole stomach acid reduce karta hai. Acidity, ulcer aur GERD mein use hota hai.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Omeprazole",
    },

    # ── Body Parts ────────────────────────────────────────────────────────────
    "brain": {
        "display_name": "Human Brain",
        "image_url":    "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=400&q=80",
        "description":  "Brain human body ka control center hai. 86 billion neurons se bana hai, sab kuch control karta hai.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Human_brain",
    },
    "lung": {
        "display_name": "Lungs",
        "image_url":    "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=400&q=80",
        "description":  "Lungs oxygen inhale aur CO2 exhale karte hain. Do lungs mein 300 million alveoli hote hain.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Lung",
    },
    "lungs": {
        "display_name": "Lungs",
        "image_url":    "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=400&q=80",
        "description":  "Lungs respiratory system ka main organ hain. Oxygen blood mein transfer karte hain.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Lung",
    },
    "liver": {
        "display_name": "Liver",
        "image_url":    "https://images.unsplash.com/photo-1559757175-0eb30cd8c063?w=400&q=80",
        "description":  "Liver body ka largest internal organ hai. Digestion, detoxification aur protein synthesis karta hai.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Liver",
    },
    "kidney": {
        "display_name": "Kidney",
        "image_url":    "https://images.unsplash.com/photo-1559757175-0eb30cd8c063?w=400&q=80",
        "description":  "Kidneys blood filter karke waste urine mein nikaalte hain. Blood pressure bhi regulate karte hain.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Kidney",
    },
    "bone": {
        "display_name": "Bone",
        "image_url":    "https://images.unsplash.com/photo-1530497610245-94d3c16cda28?w=400&q=80",
        "description":  "Bones body ko structure deti hain, organs protect karti hain aur muscles support karti hain.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Bone",
    },
    "skin": {
        "display_name": "Skin",
        "image_url":    "https://images.unsplash.com/photo-1576671081837-49000212a370?w=400&q=80",
        "description":  "Skin body ka sabse bada organ hai. Infection se protect karta hai, temperature regulate karta hai.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Skin",
    },
    "blood": {
        "display_name": "Blood",
        "image_url":    "https://images.unsplash.com/photo-1559757175-0eb30cd8c063?w=400&q=80",
        "description":  "Blood oxygen, nutrients aur waste transport karta hai. Red cells, white cells aur platelets hote hain.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Blood",
    },
    "stomach": {
        "display_name": "Stomach",
        "image_url":    "https://images.unsplash.com/photo-1576671081837-49000212a370?w=400&q=80",
        "description":  "Stomach food digest karta hai. Hydrochloric acid aur enzymes food break down karte hain.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Stomach",
    },
    "thyroid": {
        "display_name": "Thyroid",
        "image_url":    "https://images.unsplash.com/photo-1559757175-0eb30cd8c063?w=400&q=80",
        "description":  "Thyroid gland hormones produce karta hai jo metabolism aur energy regulate karte hain.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Thyroid",
    },
    "eye": {
        "display_name": "Human Eye",
        "image_url":    "https://images.unsplash.com/photo-1516302752625-fcc3c50ae61f?w=400&q=80",
        "description":  "Human eye light detect karta hai aur brain ko visual signals bhejta hai.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Human_eye",
    },
    "bacteria": {
        "display_name": "Bacteria",
        "image_url":    "https://images.unsplash.com/photo-1585435557343-3b092031a831?w=400&q=80",
        "description":  "Bacteria single-celled microorganisms hain. Kuch beneficial hain, kuch infections cause karte hain.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Bacteria",
    },
    "virus": {
        "display_name": "Virus",
        "image_url":    "https://images.unsplash.com/photo-1584483766114-2cea6facdf57?w=400&q=80",
        "description":  "Virus microscopic infectious agents hain jo living cells ke andar replicate karte hain.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Virus",
    },
    "surgery": {
        "display_name": "Surgery",
        "image_url":    "https://images.unsplash.com/photo-1530497610245-94d3c16cda28?w=400&q=80",
        "description":  "Surgery medical procedure hai jisme body tissue ko instruments se treat kiya jaata hai.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Surgery",
    },
    "dna": {
        "display_name": "DNA",
        "image_url":    "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=400&q=80",
        "description":  "DNA genetic information carry karta hai. Double helix structure hoti hai.",
        "wiki_url":     "https://en.wikipedia.org/wiki/DNA",
    },
    "inflammation": {
        "display_name": "Inflammation",
        "image_url":    "https://images.unsplash.com/photo-1576671081837-49000212a370?w=400&q=80",
        "description":  "Inflammation injury ya infection ke response mein body ki natural healing process hai.",
        "wiki_url":     "https://en.wikipedia.org/wiki/Inflammation",
    },
}


def extract_best_match(question: str) -> dict | None:
    """Sabse lamba matching keyword dhundho (longer = more specific = better)."""
    q = question.lower()
    best_keyword = ""
    best_data = None

    for keyword, data in MEDICAL_DATA.items():
        if keyword in q and len(keyword) > len(best_keyword):
            best_keyword = keyword
            best_data = data

    return best_data


def get_medical_image(question: str) -> dict | None:
    """
    Main function — app.py yahi call karta hai.
    No network calls — instant response, always works.
    Returns: { medicine_name, wiki_title, image_url, description, wiki_url }
    Ya None agar koi keyword match nahi hua.
    """
    data = extract_best_match(question)
    if not data:
        return None

    return {
        "medicine_name": data["display_name"],
        "wiki_title":    data["display_name"],
        "image_url":     data["image_url"],
        "description":   data["description"],
        "wiki_url":      data["wiki_url"],
    }
