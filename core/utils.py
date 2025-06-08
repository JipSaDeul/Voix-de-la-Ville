# core.utils
from typing import Tuple, Optional

import spacy
from argostranslate import translate
from charset_normalizer import detect
from django.http import HttpRequest

from .models import Comment
from .models import Vote

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


# Load the spaCy model (e.g., en_core_web_sm) for natural language processing
nlp = spacy.load("en_core_web_sm")


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


from typing import Dict


def nlp_categorize(text: str) -> Dict[str, str]:
    """
    Categorizes the input text into one of the predefined categories based on keywords.
    If the text is in French, it will be translated to English first.

    :param text: The input text to be categorized.
    :return: A dictionary containing the 'name' and 'description' of the category
             with the highest match. If no category is matched, returns "other".
    """

    # Detect the language of the text (default to English)
    language = detect(text.encode('utf-8'))

    # If the text is in French, translate it to English
    if language == 'fr':
        text = auto_translate(text, from_lang="fr", to_lang="en")

    # Process the text using the NLP model (spaCy)
    doc = nlp(text)

    # Define the categories with corresponding keywords and descriptions
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

    # Initialize the category counts
    categories_count = {key: 0 for key in categories}

    # Process each token in the document and count matches with keywords
    for token in doc:
        for category, data in categories.items():
            if token.lemma_ in data["keywords"]:
                categories_count[category] += 1

    # Find the category with the highest count
    max_category = max(categories_count, key=categories_count.get)

    # If no category has any matches, return the "other" category
    if categories_count[max_category] == 0:
        return categories["other"]  # If no category matched, return the "other" category

    # Return the name and description of the category with the highest count
    return {
        "name": categories[max_category]["name"],
        "description": categories[max_category]["description"]
    }





def build_report_data(reports):
    """
    Helper function to build data for each report including vote count and related fields.

    :param reports: A queryset of Report objects.
    :return: A list of dictionaries containing the report details.
    """
    data = []
    for r in reports:
        # Get vote count either from annotate or manually
        vote_count = r.vote_count if hasattr(r, 'vote_count') else Vote.objects.filter(report=r).count()

        data.append({
            "id": r.id,
            "title": r.title,
            "description": r.description,
            "vote_count": vote_count,  # Handle vote count
            "status": r.status,
            "image_url": r.image.url if r.image else None,  # Check if image exists
            "category": r.category.name if r.category else None,  # Access related category name
            "user_email": r.user.email if r.user else None,  # Access related user's email
            "user_name": r.user.username if r.user else None,  # Access related user's username
            "created_at": r.created_at,
        })
    return data
