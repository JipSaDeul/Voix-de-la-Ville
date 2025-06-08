# scripts/download_spacy_model.py

import spacy

def download_spacy_model():
    try:
        # Try to download the spaCy model
        print("Downloading spaCy 'en_core_web_sm' model...")
        spacy.cli.download("en_core_web_sm")
        print("Model downloaded successfully.")
    except Exception as e:
        print(f"Error while downloading model: {e}")

if __name__ == "__main__":
    download_spacy_model()
