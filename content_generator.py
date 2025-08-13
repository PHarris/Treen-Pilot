# content_generator.py
import os
from dotenv import load_dotenv
from openai import OpenAI
from generate_copy_enhanced import generate_social_media_caption

load_dotenv()

# Create the OpenAI client once (v1.x style). Do NOT pass proxies here.
_client = None
def _get_client():
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
        _client = OpenAI(api_key=api_key)
    return _client


def generate_social_copy(prompt: str) -> str:
    """
    Returns a caption string.
    - Uses OpenAI v1 SDK correctly.
    - Falls back to your template generator if no key or on any error.
    """
    client = _get_client()
    if client is None:
        # Fallback: use your template generator (keeps MVP working without a key)
        return generate_social_media_caption(prompt, platform="instagram", tone="engaging", trend="")

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Act as if you're the best social copywriter in the world."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.8,
            max_tokens=220,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        # Log for Render logs; keep the app robust
        print(f"OpenAI text error: {e}")
        return generate_social_media_caption(prompt, platform="instagram", tone="engaging", trend="")
