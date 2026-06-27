import os
import httpx

api_key = os.getenv("MISTRAL_API_KEY")

def call_mistral(prompt: str) -> str:
    if not api_key:
        raise ValueError("MISTRAL_API_KEY is not set.")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "mistral-large-latest",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            "https://api.mistral.ai/v1/chat/completions",
            json=payload,
            headers=headers
        )
    if response.status_code != 200:
        raise RuntimeError(f"Mistral API returned {response.status_code}: {response.text}")
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()

def detect_language(text: str) -> str:
    """
    Detects if the query language is English, Hindi, or Kannada using Mistral AI.
    """
    if not api_key:
        return "english"  # Fallback
        
    try:
        prompt = (
            "Analyze the following text and detect if the language is English, Hindi, or Kannada. "
            "Return only one word in lowercase: 'english', 'hindi', or 'kannada'. "
            "If it is mixed or unclear, default to 'english'.\n\n"
            f"Text: {text}"
        )
        lang = call_mistral(prompt).lower()
        if lang in ["english", "hindi", "kannada"]:
            return lang
        return "english"
    except Exception:
        return "english"

def translate_to_english(text: str, source_lang: str) -> str:
    """
    Translates Hindi or Kannada text to English using Mistral AI.
    """
    if not text or source_lang == "english" or not api_key:
        return text
        
    try:
        prompt = (
            f"Translate the following agricultural text from {source_lang.title()} to English. "
            "Do not add any explanations, introductory text, or notes. Return ONLY the direct translation:\n\n"
            f"{text}"
        )
        return call_mistral(prompt)
    except Exception:
        return text

def translate_from_english(text: str, target_lang: str) -> str:
    """
    Translates English response back to Hindi or Kannada, keeping markdown formatting intact.
    """
    if not text or target_lang == "english" or not api_key:
        return text
        
    try:
        prompt = (
            f"Translate the following expert agricultural response from English to {target_lang.title()}.\n"
            "CRITICAL INSTRUCTIONS:\n"
            "1. Maintain all markdown formatting, tables, lists, bullet points, and bold text exactly as they are.\n"
            "2. Keep agricultural terms or scheme names in parentheses or transliterated if appropriate (e.g. 'mandi', 'MSP', 'PM-KISAN' should stay readable).\n"
            "3. Do not add any introductory or concluding remarks from the translator. Return ONLY the translated output.\n\n"
            f"Text to translate:\n{text}"
        )
        return call_mistral(prompt)
    except Exception:
        return text

