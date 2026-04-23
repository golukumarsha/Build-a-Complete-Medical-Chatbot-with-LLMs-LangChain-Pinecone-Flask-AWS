"""
seed_db.py — MongoDB mein sample medical data dalo
Run karo: python seed_db.py
"""

from src.database import insert_many_medicines, get_stats
from dotenv import load_dotenv
load_dotenv()


SAMPLE_DATA = [
    # ─── DISEASES ───────────────────────────────────────────────────────────
    {
        "name": "Diabetes",
        "category": "Disease",
        "description": "Ek chronic condition jisme body blood sugar (glucose) ko properly regulate nahi kar paati. Type 1 mein insulin nahi banta, Type 2 mein insulin resistance hoti hai.",
        "symptoms": ["frequent urination", "excessive thirst", "fatigue", "blurred vision", "slow healing wounds", "unexplained weight loss"],
        "treatment": ["insulin therapy", "metformin", "diet control", "regular exercise", "blood sugar monitoring"],
        "side_effects": [],
        "dosage": "",
        "prevention": ["healthy diet", "regular exercise", "weight management", "avoid sugary foods"],
        "wiki_url": "https://en.wikipedia.org/wiki/Diabetes"
    },
    {
        "name": "Hypertension",
        "category": "Disease",
        "description": "High blood pressure — jab blood vessels mein blood ka pressure consistently 140/90 mmHg se upar ho. 'Silent killer' bhi kehte hain kyunki symptoms nahi hote.",
        "symptoms": ["headache", "dizziness", "shortness of breath", "nosebleeds", "chest pain", "often no symptoms"],
        "treatment": ["amlodipine", "lisinopril", "diet changes", "exercise", "reduce salt intake"],
        "side_effects": [],
        "dosage": "",
        "prevention": ["low salt diet", "no smoking", "limit alcohol", "stress management", "regular exercise"],
        "wiki_url": "https://en.wikipedia.org/wiki/Hypertension"
    },
    {
        "name": "Asthma",
        "category": "Disease",
        "description": "Airways ki chronic inflammatory disease jisme breathing difficult ho jaati hai. Airways narrow aur swollen ho jaati hain, extra mucus banta hai.",
        "symptoms": ["wheezing", "shortness of breath", "chest tightness", "coughing especially at night", "difficulty breathing"],
        "treatment": ["inhaled corticosteroids", "bronchodilators", "salbutamol inhaler", "avoid triggers"],
        "side_effects": [],
        "dosage": "",
        "prevention": ["avoid allergens", "no smoking", "air purifier", "regular medication"],
        "wiki_url": "https://en.wikipedia.org/wiki/Asthma"
    },
    {
        "name": "Pneumonia",
        "category": "Disease",
        "description": "Lungs ka infection jo bacteria, virus ya fungi se hota hai. Alveoli (air sacs) mein fluid ya pus bhar jaata hai.",
        "symptoms": ["high fever", "chills", "cough with phlegm", "chest pain", "difficulty breathing", "fatigue"],
        "treatment": ["antibiotics (bacterial)", "antiviral drugs", "rest", "fluids", "hospitalization if severe"],
        "side_effects": [],
        "dosage": "",
        "prevention": ["pneumonia vaccine", "flu vaccine", "good hygiene", "no smoking"],
        "wiki_url": "https://en.wikipedia.org/wiki/Pneumonia"
    },
    {
        "name": "Malaria",
        "category": "Disease",
        "description": "Plasmodium parasite se hone wali bimari jo infected Anopheles mosquito ke kaatne se failti hai. India mein bahut common hai.",
        "symptoms": ["cyclical fever", "chills", "sweating", "headache", "nausea", "muscle pain", "fatigue"],
        "treatment": ["chloroquine", "artemisinin-based therapy", "quinine", "primaquine"],
        "side_effects": [],
        "dosage": "",
        "prevention": ["mosquito nets", "insect repellent", "antimalarial drugs", "eliminate stagnant water"],
        "wiki_url": "https://en.wikipedia.org/wiki/Malaria"
    },
    {
        "name": "Tuberculosis",
        "category": "Disease",
        "description": "Mycobacterium tuberculosis bacteria se hone wali infectious disease. Mainly lungs ko affect karti hai lekin body ke dusre parts bhi ho sakti hai.",
        "symptoms": ["persistent cough >3 weeks", "blood in cough", "night sweats", "fever", "weight loss", "fatigue"],
        "treatment": ["isoniazid", "rifampicin", "pyrazinamide", "ethambutol", "6 month course mandatory"],
        "side_effects": [],
        "dosage": "",
        "prevention": ["BCG vaccine", "good ventilation", "cover mouth while coughing", "complete treatment course"],
        "wiki_url": "https://en.wikipedia.org/wiki/Tuberculosis"
    },
    {
        "name": "Dengue",
        "category": "Disease",
        "description": "Aedes mosquito se failne wala viral fever. India mein monsoon season mein bahut cases aate hain.",
        "symptoms": ["high fever", "severe headache", "pain behind eyes", "joint and muscle pain", "skin rash", "mild bleeding"],
        "treatment": ["paracetamol for fever", "ORS for hydration", "rest", "no aspirin or ibuprofen", "platelet monitoring"],
        "side_effects": [],
        "dosage": "",
        "prevention": ["avoid mosquito bites", "full sleeve clothes", "mosquito repellent", "no stagnant water"],
        "wiki_url": "https://en.wikipedia.org/wiki/Dengue_fever"
    },
    {
        "name": "Arthritis",
        "category": "Disease",
        "description": "Joints ki inflammation jisme pain, stiffness aur swelling hoti hai. Osteoarthritis (wear & tear) aur Rheumatoid arthritis (autoimmune) dono common hain.",
        "symptoms": ["joint pain", "stiffness", "swelling", "redness", "reduced range of motion", "morning stiffness"],
        "treatment": ["NSAIDs", "physical therapy", "corticosteroids", "DMARDs for RA", "surgery in severe cases"],
        "side_effects": [],
        "dosage": "",
        "prevention": ["exercise", "healthy weight", "protect joints", "calcium and vitamin D"],
        "wiki_url": "https://en.wikipedia.org/wiki/Arthritis"
    },

    # ─── MEDICINES ───────────────────────────────────────────────────────────
    {
        "name": "Paracetamol",
        "category": "Medicine",
        "description": "Sabse common pain reliever aur fever reducer. Acetaminophen bhi kehte hain. OTC (over the counter) milti hai.",
        "symptoms": [],
        "treatment": ["fever", "headache", "body pain", "toothache", "cold & flu symptoms"],
        "side_effects": ["liver damage if overdose", "nausea", "rash (rare)", "allergic reaction (rare)"],
        "dosage": "500mg-1000mg har 4-6 ghante mein, max 4g/day",
        "prevention": [],
        "wiki_url": "https://en.wikipedia.org/wiki/Paracetamol"
    },
    {
        "name": "Ibuprofen",
        "category": "Medicine",
        "description": "NSAID (Non-steroidal anti-inflammatory drug) jo pain, fever aur inflammation teeno mein kaam karti hai.",
        "symptoms": [],
        "treatment": ["pain", "fever", "inflammation", "arthritis", "menstrual cramps", "headache"],
        "side_effects": ["stomach upset", "ulcers with long use", "kidney issues", "avoid in pregnancy", "avoid in dengue"],
        "dosage": "200mg-400mg har 6-8 ghante mein, khane ke saath",
        "prevention": [],
        "wiki_url": "https://en.wikipedia.org/wiki/Ibuprofen"
    },
    {
        "name": "Amoxicillin",
        "category": "Medicine",
        "description": "Broad-spectrum penicillin antibiotic jo bacterial infections ke liye use hoti hai. Doctor ki prescription zaroori hai.",
        "symptoms": [],
        "treatment": ["ear infection", "throat infection", "urinary tract infection", "pneumonia", "skin infections"],
        "side_effects": ["diarrhea", "nausea", "skin rash", "allergic reaction", "yeast infection"],
        "dosage": "250mg-500mg teen baar daily, 5-10 din ka course",
        "prevention": [],
        "wiki_url": "https://en.wikipedia.org/wiki/Amoxicillin"
    },
    {
        "name": "Metformin",
        "category": "Medicine",
        "description": "Type 2 Diabetes ki first-line medicine. Blood sugar kam karta hai liver mein glucose production rok ke.",
        "symptoms": [],
        "treatment": ["type 2 diabetes", "prediabetes", "PCOS"],
        "side_effects": ["nausea", "diarrhea", "stomach upset", "lactic acidosis (rare)", "vitamin B12 deficiency"],
        "dosage": "500mg-1000mg din mein 2 baar, khane ke saath",
        "prevention": [],
        "wiki_url": "https://en.wikipedia.org/wiki/Metformin"
    },
    {
        "name": "Aspirin",
        "category": "Medicine",
        "description": "Salicylate drug jo pain, fever aur inflammation mein kaam karta hai. Heart attack prevention ke liye bhi use hota hai (low dose).",
        "symptoms": [],
        "treatment": ["pain", "fever", "heart attack prevention", "stroke prevention", "blood clot prevention"],
        "side_effects": ["stomach bleeding", "ulcers", "tinnitus (high dose)", "Reye syndrome (children)", "allergic reaction"],
        "dosage": "Pain ke liye: 325-650mg | Heart prevention: 75-100mg daily",
        "prevention": [],
        "wiki_url": "https://en.wikipedia.org/wiki/Aspirin"
    },
    {
        "name": "Omeprazole",
        "category": "Medicine",
        "description": "Proton pump inhibitor (PPI) jo stomach acid production kam karta hai. Acidity, GERD aur ulcers ke liye use hota hai.",
        "symptoms": [],
        "treatment": ["acidity", "GERD", "stomach ulcers", "H. pylori infection", "heartburn"],
        "side_effects": ["headache", "diarrhea", "nausea", "long term: low magnesium, B12 deficiency", "bone fracture risk"],
        "dosage": "20mg-40mg subah khane se 30 minute pehle",
        "prevention": [],
        "wiki_url": "https://en.wikipedia.org/wiki/Omeprazole"
    },
    {
        "name": "Cetirizine",
        "category": "Medicine",
        "description": "Second-generation antihistamine jo allergy symptoms treat karta hai. Pehle generation se kam neend aati hai.",
        "symptoms": [],
        "treatment": ["allergic rhinitis", "hay fever", "urticaria (hives)", "itching", "watery eyes", "sneezing"],
        "side_effects": ["mild drowsiness", "dry mouth", "headache", "fatigue"],
        "dosage": "10mg ek baar daily, raat ko lena better hai",
        "prevention": [],
        "wiki_url": "https://en.wikipedia.org/wiki/Cetirizine"
    },
    {
        "name": "Azithromycin",
        "category": "Medicine",
        "description": "Macrolide antibiotic jo respiratory, skin aur sexually transmitted infections treat karta hai. 3-5 din ka short course hota hai.",
        "symptoms": [],
        "treatment": ["chest infection", "throat infection", "typhoid", "chlamydia", "community-acquired pneumonia"],
        "side_effects": ["nausea", "diarrhea", "stomach pain", "liver issues (rare)", "QT prolongation (heart)"],
        "dosage": "500mg pehle din, phir 250mg 4 din tak",
        "prevention": [],
        "wiki_url": "https://en.wikipedia.org/wiki/Azithromycin"
    },

    # ─── SUPPLEMENTS ─────────────────────────────────────────────────────────
    {
        "name": "Vitamin D",
        "category": "Supplement",
        "description": "Fat-soluble vitamin jo calcium absorption, bone health aur immune function ke liye zaroori hai. India mein deficiency bahut common hai.",
        "symptoms": ["bone pain", "muscle weakness", "fatigue", "frequent infections", "depression"],
        "treatment": ["vitamin D deficiency", "rickets", "osteoporosis prevention", "immune support"],
        "side_effects": ["hypercalcemia if overdose", "nausea", "weakness", "kidney stones (excess)"],
        "dosage": "1000-2000 IU daily (maintenance) | 60,000 IU weekly (deficiency treatment)",
        "prevention": [],
        "wiki_url": "https://en.wikipedia.org/wiki/Vitamin_D"
    },
    {
        "name": "Vitamin C",
        "category": "Supplement",
        "description": "Water-soluble antioxidant vitamin jo immune system strengthen karta hai, wound healing mein madad karta hai aur iron absorption badhata hai.",
        "symptoms": ["frequent colds", "slow wound healing", "fatigue", "scurvy (deficiency)"],
        "treatment": ["immune boost", "scurvy", "iron absorption", "skin health", "antioxidant"],
        "side_effects": ["stomach upset (high dose)", "diarrhea (>2g/day)", "kidney stones (very high dose)"],
        "dosage": "500mg-1000mg daily, khane ke saath",
        "prevention": [],
        "wiki_url": "https://en.wikipedia.org/wiki/Vitamin_C"
    },
    {
        "name": "Zinc",
        "category": "Supplement",
        "description": "Essential mineral jo immune function, wound healing, DNA synthesis aur taste/smell sense ke liye zaroori hai. COVID-19 mein bhi use hua.",
        "symptoms": ["frequent infections", "slow wound healing", "hair loss", "loss of taste/smell", "poor growth"],
        "treatment": ["zinc deficiency", "cold duration reduce", "immune support", "skin health", "diarrhea in children"],
        "side_effects": ["nausea (empty stomach)", "copper deficiency (long term high dose)", "metallic taste"],
        "dosage": "8-11mg daily (RDA) | 25-50mg therapeutic dose",
        "prevention": [],
        "wiki_url": "https://en.wikipedia.org/wiki/Zinc"
    },
]


if __name__ == "__main__":
    print("🏥 MediBot Database — Sample Data Loading...")
    print("=" * 50)

    result = insert_many_medicines(SAMPLE_DATA)

    print(f"✅ Successfully added : {result['success']} records")
    print(f"⚠️  Already existed   : {result['failed']} records")

    if result["errors"]:
        print("\nMessages:")
        for e in result["errors"]:
            print(f"  → {e}")

    print("\n📊 Database Stats:")
    stats = get_stats()
    print(f"  Total     : {stats['total']}")
    print(f"  Diseases  : {stats['diseases']}")
    print(f"  Medicines : {stats['medicines']}")
    print(f"  Supplements: {stats['supplements']}")
    print("\n✅ Database ready!")
