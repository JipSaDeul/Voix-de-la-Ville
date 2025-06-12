# core.utils
from typing import Dict, Optional, Tuple

import spacy
from argostranslate import translate
from django.http import HttpRequest
from django.utils.formats import date_format
from django.utils.timezone import localtime
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from langdetect import DetectorFactory, detect_langs, LangDetectException

from .cities.helper import get_city_info_by_zipcodes
from .models import Comment, Vote, AdminComment

"""
Models Related
"""


def get_user_id(request: HttpRequest) -> Optional[int]:
    """
    Get the current authenticated user's ID.
    If the user is not authenticated, return None.

    :param request: The HTTP request object, which contains the user session.
    :return: The user's ID if authenticated, else None.
    """
    if request.user.is_authenticated:
        return request.user.id  # Return the ID of the authenticated user
    else:
        return None  # Return None if the user is not authenticated


def create_or_update_comment(user_id: int, report_id: int, content: str) -> Tuple[Optional[Comment], bool]:
    """
    Create or update a comment for a user on a specific report.
    If a comment already exists, it will be updated with the new content.

    :param user_id: The ID of the user creating or updating the comment.
    :param report_id: The ID of the report to which the comment belongs.
    :param content: The content of the comment.
    :return: The created or updated comment object and a boolean indicating if the comment was created.
    """
    try:
        # Ensure the types are correct before proceeding
        if not isinstance(user_id, int) or not isinstance(report_id, int) or not isinstance(content, str):
            raise TypeError("Invalid input type")

        # Try to update or create the comment
        comment, created = Comment.objects.update_or_create(
            user_id=user_id, report_id=report_id, defaults={"content": content}
        )
        return comment, created

    except TypeError:
        # If there is a TypeError, return None and False
        return None, False


def create_or_update_admin_comment(admin_id: int, report_id: int, content: str) -> Tuple[Optional[AdminComment], bool]:
    """
    Create or update an admin comment on a specific report.
    If an admin comment already exists for this admin and report, update it.

    :param admin_id: The ID of the admin (Django auth user).
    :param report_id: The ID of the report.
    :param content: The comment content.
    :return: Tuple of (AdminComment object or None, is_created: bool)
    """
    try:
        if not isinstance(admin_id, int) or not isinstance(report_id, int) or not isinstance(content, str):
            raise TypeError("Invalid input type")

        comment, created = AdminComment.objects.update_or_create(
            admin_id=admin_id,
            report_id=report_id,
            defaults={"content": content}
        )
        return comment, created

    except TypeError:
        return None, False


def create_vote(user_id: int, report_id: int) -> Tuple[Optional[Vote], bool]:
    """
    Create a vote for a user on a specific report.
    If the user has already voted, it will return the existing vote.

    :param user_id: The ID of the user casting the vote.
    :param report_id: The ID of the report being voted on.
    :return: The created or existing vote object and a boolean indicating if the vote was created.
    """
    try:
        # Ensure the types are correct before proceeding
        if not isinstance(user_id, int) or not isinstance(report_id, int):
            raise TypeError("Invalid input type")

        # Try to create or get the vote
        vote, created = Vote.objects.get_or_create(user_id=user_id, report_id=report_id)
        return vote, created

    except TypeError:
        # If there is a TypeError, return None and False
        return None, False


def build_report_data(reports):
    """
    Build data for each report including vote count and city info from zipcode.

    :param reports: A queryset of Report objects.
    :return: A list of dictionaries containing the report details.
    """
    data = []

    # Collect unique zipcodes
    zipcodes = list({r.zipcode for r in reports if r.zipcode is not None})

    # Build a mapping from zipcode -> city info
    zipcode_info_map = {
        str(item["zipcode"]): item
        for item in get_city_info_by_zipcodes(zipcodes)
    }

    for r in reports:
        vote_count = r.vote_count if hasattr(r, 'vote_count') else Vote.objects.filter(report=r).count()

        z_info = zipcode_info_map.get(str(r.zipcode), {"zipcode": "/", "place": "/", "province": "Out seas"})

        data.append({
            "id": r.id,
            "title": r.title,
            "description": r.description,
            "vote_count": vote_count,
            "status": r.get_status_display(),
            "zipcode": z_info["zipcode"],
            "place": z_info["place"],
            "province": z_info["province"],
            "image_url": r.image.url if r.image else None,
            "category": r.category.name if r.category else None,
            "user_email": r.user.email if r.user else None,
            "user_name": r.user.username if r.user else None,
            "created_at": date_format(localtime(r.created_at), format='DATETIME_FORMAT'),
        })
    return data


"""
Translations Related
"""

# Load the spaCy model (e.g., en_core_web_sm) for natural language processing
nlp = spacy.load("en_core_web_sm")
tokenizer = AutoTokenizer.from_pretrained("unitary/toxic-bert")
model = AutoModelForSequenceClassification.from_pretrained("unitary/toxic-bert")
toxic_classifier = pipeline("text-classification", model=model, tokenizer=tokenizer, device=-1)

DetectorFactory.seed = 0


def detect_language(text: str) -> str:
    """
    Detect the language of a given text, prioritizing English and French.
    If detected language is not in allowed list, fallback to English.
    """
    allowed = {"en", "fr", "de", "es"}
    try:
        # detect_langs returns a list of possible languages with probabilities
        lang_probs = detect_langs(text)
        for lang in lang_probs:
            if lang.lang in allowed:
                return lang.lang
        return "en"  # fallback if no allowed language found
    except LangDetectException:
        return "en"


def auto_translate(text: str, from_lang: str = "fr", to_lang: str = "en") -> str:
    """
    Automatically translates the input text from one language to another using Argos Translate.

    :param text: The input text to be translated.
    :param from_lang: The language code of the source language (default is French).
    :param to_lang: The language code of the target language (default is English).
    :return: The translated text if translation is available, otherwise the original text.
    """

    # Get the list of installed languages in the translation system
    installed_languages = translate.get_installed_languages()

    # Find the source and target languages from the installed languages
    from_lang_obj = next((l for l in installed_languages if l.code == from_lang), None)
    to_lang_obj = next((l for l in installed_languages if l.code == to_lang), None)

    # If both source and target languages are found in the installed languages, perform the translation
    if from_lang_obj and to_lang_obj:
        translation = from_lang_obj.get_translation(to_lang_obj)
        return translation.translate(text)  # Return the translated text

    # If translation is not possible, return the original text
    return text


def to_eng(text: str) -> str:
    lang_code = detect_language(text)

    if lang_code != "en":
        return auto_translate(text, from_lang=lang_code, to_lang="en")
    return text


categories = {
    "infrastructure": {
        "name": "Infrastructure",
        "description": "Issues related to roads, streets, sidewalks, and other infrastructure concerns.",
        "keywords": ["road", "street", "sidewalk", "pothole", "repair", "construction"]
    },
    "environment": {
        "name": "Environment",
        "description": "Concerns related to noise, pollution, cleanliness, and the environment.",
        "keywords": ["noise", "sound", "pollution", "clean", "garbage", "smell", "dust", "cleanliness"]
    },
    "traffic": {
        "name": "Traffic",
        "description": "Traffic-related issues such as congestion, parking, and traffic signals.",
        "keywords": ["traffic", "signal", "congestion", "parking", "bus", "car", "bus stop", "traffic jam"]
    },
    "security": {
        "name": "Security",
        "description": "Security-related issues like crime, theft, and vandalism.",
        "keywords": ["theft", "crime", "robbery", "assault", "security", "police", "danger", "vandalism"]
    },
    "public_service": {
        "name": "Public Service",
        "description": "Issues regarding public services like water, electricity, and emergency services.",
        "keywords": ["water", "electricity", "sewer", "fire", "service", "maintenance", "emergency"]
    },
    "health": {
        "name": "Health",
        "description": "Health-related issues such as disease, sanitation, and medical services.",
        "keywords": ["health", "hospital", "doctor", "sanitation", "disease", "cleanliness", "infection"]
    },
    "other": {
        "name": "Other",
        "description": "Any issue that doesn't fall under the standard categories.",
        "keywords": []
    }
}


def nlp_categorize(text: str) -> Optional[Dict[str, str]]:
    text_en = to_eng(text).strip()
    if not text_en:
        return None

    doc = nlp(text_en)

    print(doc)
    # Nonsense
    meaningful_tokens = [
        t for t in doc
        if t.is_alpha and len(t.text) > 2 and t.has_vector
    ]
    print(meaningful_tokens)

    if len(meaningful_tokens) < 1:
        return None

    counts = {key: 0 for key in categories}
    for token in meaningful_tokens:
        for key, info in categories.items():
            if token.lemma_.lower() in info["keywords"]:
                counts[key] += 1

    best_match = max(counts, key=counts.get)
    if counts[best_match] == 0:
        return categories["other"]

    return {
        "name": categories[best_match]["name"],
        "description": categories[best_match]["description"]
    }


def detect_profanity(text: str, threshold: float = 0.8) -> Dict[str, object]:
    """
    Detects whether the input text contains offensive or toxic language.
    Handles language detection and automatic translation before classification.

    :param text: The input text to analyze.
    :param threshold: The score threshold to consider text as toxic.
    :return: Dictionary with `is_toxic`, `score`, `label` (if applicable).
    """

    text_en = to_eng(text)

    result = toxic_classifier(text_en)[0]

    return {
        "is_toxic": result["score"] >= threshold,
        "score": result["score"]
    }
