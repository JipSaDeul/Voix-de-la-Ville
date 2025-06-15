# scripts/download_models.py

import spacy


def download_spacy_model():
    try:
        # Try to download the spaCy model
        print("Downloading spaCy 'en_core_web_md' model...")
        spacy.cli.download("en_core_web_md")
        print("Model downloaded successfully.")
    except Exception as e:
        print(f"Error while downloading model: {e}")


from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline


def download_toxic_bert_model():
    try:
        print("Downloading Hugging Face toxic-bert model...")
        tokenizer = AutoTokenizer.from_pretrained("unitary/toxic-bert")
        model = AutoModelForSequenceClassification.from_pretrained("unitary/toxic-bert")
        _ = pipeline("text-classification", model=model, tokenizer=tokenizer, device=-1)  # force CPU
        print("Download complete.")
    except Exception as e:
        print(f"Download failed: {e}")


from argostranslate import package


def download_argos_models(language_pairs):
    try:
        print("Checking Argos Translate models...")

        installed_pairs = {
            (pkg.from_code, pkg.to_code)
            for pkg in package.get_installed_packages()
        }

        available_packages = package.get_available_packages()

        for from_code, to_code in language_pairs:
            if (from_code, to_code) in installed_pairs:
                print(f"Argos model {from_code}→{to_code} already installed.")
                continue

            print(f"Downloading Argos model {from_code}→{to_code}... (may take a while)")
            pkg = next(
                p for p in available_packages if p.from_code == from_code and p.to_code == to_code
            )
            package_path = pkg.download()
            package.install_from_path(package_path)
            print(f"Installed Argos model {from_code}→{to_code}.")

    except Exception as e:
        print(f"[argos] Download/install failed: {e}")


if __name__ == "__main__":
    download_spacy_model()
    download_toxic_bert_model()
    download_argos_models([
        ("fr", "en"),
        # ("de", "en"),
        ("es", "en"),
        ("en", "fr")
    ])
