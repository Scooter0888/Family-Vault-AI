"""
Translation Helper Functions
Translate interview questions to different languages using OpenAI
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Supported languages
SUPPORTED_LANGUAGES = {
    "English": "en",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Italian": "it",
    "Portuguese": "pt",
    "Chinese (Simplified)": "zh",
    "Japanese": "ja",
    "Korean": "ko",
    "Arabic": "ar",
    "Hindi": "hi",
    "Russian": "ru",
    "Vietnamese": "vi",
    "Polish": "pl",
    "Dutch": "nl",
    "Greek": "el",
    "Hebrew": "he",
    "Turkish": "tr",
    "Swedish": "sv",
    "Norwegian": "no",
    "Danish": "da",
    "Finnish": "fi"
}


def translate_text(text, target_language="Spanish"):
    """
    Translate text to target language using OpenAI

    Args:
        text (str): Text to translate
        target_language (str): Target language name (e.g., "Spanish", "French")

    Returns:
        str: Translated text, or original text if translation fails
    """

    # If target is English, return original
    if target_language == "English":
        return text

    try:
        # Create translation prompt
        prompt = f"""Translate the following text to {target_language}.
Maintain the same tone and meaning. Return ONLY the translation, no explanations.

Text to translate:
{text}"""

        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a professional translator. Translate text to {target_language} accurately while preserving meaning and tone."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,  # Lower temperature for more consistent translations
            max_tokens=500
        )

        # Extract translation
        translation = response.choices[0].message.content.strip()
        return translation

    except Exception as e:
        print(f"Translation error: {e}")
        return text  # Return original text if translation fails


def translate_question(question, target_language="Spanish"):
    """
    Translate an interview question to target language

    Args:
        question (str): Question text
        target_language (str): Target language name

    Returns:
        str: Translated question
    """
    return translate_text(question, target_language)


def test_translation():
    """Test translation functionality"""

    test_question = "What were your parents' full names? When and where were they born?"

    print("Testing translation...")
    print(f"\nOriginal (English): {test_question}")

    # Test Spanish translation
    spanish = translate_question(test_question, "Spanish")
    print(f"\nSpanish: {spanish}")

    # Test French translation
    french = translate_question(test_question, "French")
    print(f"\nFrench: {french}")


if __name__ == "__main__":
    test_translation()
