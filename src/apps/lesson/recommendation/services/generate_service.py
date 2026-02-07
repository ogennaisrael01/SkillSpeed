
from django.conf import settings

import json

MODEL = "gemini-3-flash-preview"

def generate_recommendations(prompt: str) -> str:

    try:
        from google import genai
    except ImportError:
        raise ImportError("No module genai")
    
    api_key = getattr(settings, "GEMINI_API_KEY", None)
    if api_key is None:
        raise AttributeError("No Attribut named GEMINI API KEY")
    client = genai.Client(api_key=api_key)
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )
    except Exception as e:
        raise RuntimeError(f"Error generatin GEMINI context: {str(e)}")
    
    if not response or not getattr(response, "text"):
        raise RuntimeError("GEMINI returned not text")
    json_response = json.loads(response.text)
    return json_response
