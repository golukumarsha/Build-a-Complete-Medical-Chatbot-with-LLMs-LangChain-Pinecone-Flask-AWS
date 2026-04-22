"""
image_helper.py — Medical question ke liye relevant image fetch karta hai
Wikipedia REST API use karta hai — free, no API key needed
"""

import requests
import re


# Common medical keywords → Wikipedia article mapping
MEDICAL_IMAGE_MAP = {
    "heart": "Heart",
    "cardiac": "Heart",
    "diabetes": "Diabetes",
    "diabetic": "Diabetes",
    "brain": "Human_brain",
    "neuron": "Neuron",
    "liver": "Liver",
    "kidney": "Kidney",
    "lung": "Lung",
    "lungs": "Lung",
    "asthma": "Asthma",
    "cancer": "Cancer",
    "tumor": "Tumor",
    "blood": "Blood",
    "red blood cell": "Red_blood_cell",
    "white blood cell": "White_blood_cell",
    "dna": "DNA",
    "cell": "Cell_(biology)",
    "bacteria": "Bacteria",
    "virus": "Virus",
    "bone": "Bone",
    "muscle": "Muscle",
    "skin": "Skin",
    "eye": "Human_eye",
    "ear": "Ear",
    "stomach": "Stomach",
    "intestine": "Intestine",
    "spine": "Vertebral_column",
    "hypertension": "Hypertension",
    "blood pressure": "Blood_pressure",
    "cholesterol": "Cholesterol",
    "fever": "Fever",
    "infection": "Infection",
    "inflammation": "Inflammation",
    "fracture": "Bone_fracture",
    "arthritis": "Arthritis",
    "depression": "Depression_(mood)",
    "anxiety": "Anxiety",
    "alzheimer": "Alzheimer's_disease",
    "parkinson": "Parkinson's_disease",
    "stroke": "Stroke",
    "pneumonia": "Pneumonia",
    "covid": "COVID-19",
    "malaria": "Malaria",
    "tuberculosis": "Tuberculosis",
    "hiv": "HIV",
    "aids": "AIDS",
    "thyroid": "Thyroid",
    "insulin": "Insulin",
    "vaccine": "Vaccine",
    "antibiotic": "Antibiotic",
    "surgery": "Surgery",
    "anatomy": "Human_body",
}


def extract_keyword(question: str) -> str | None:
    """Question se medical keyword dhundho"""
    q_lower = question.lower()
    for keyword, article in MEDICAL_IMAGE_MAP.items():
        if keyword in q_lower:
            return article
    return None


def get_wikipedia_image(article_title: str) -> dict | None:
    """
    Wikipedia REST API se article ka main image + summary fetch karo
    Returns: {"image_url": ..., "caption": ..., "wiki_url": ...} ya None
    """
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{article_title}"
        headers = {"User-Agent": "MedicalChatbot/1.0 (educational project)"}
        resp = requests.get(url, headers=headers, timeout=5)

        if resp.status_code != 200:
            return None

        data = resp.json()

        # Image check
        thumbnail = data.get("thumbnail", {})
        image_url = thumbnail.get("source")

        if not image_url:
            return None

        # Higher resolution image
        image_url = re.sub(r"/\d+px-", "/400px-", image_url)

        return {
            "image_url": image_url,
            "caption": data.get("description", article_title.replace("_", " ")),
            "wiki_url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
            "title": data.get("title", article_title.replace("_", " "))
        }

    except Exception:
        return None


def get_medical_image(question: str) -> dict | None:
    """
    Main function — question se image dhundho
    Returns image info dict ya None
    """
    article = extract_keyword(question)
    if not article:
        return None
    return get_wikipedia_image(article)
