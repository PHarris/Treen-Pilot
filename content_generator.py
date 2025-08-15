# content_generator.py
import os
from dotenv import load_dotenv
from gradio_client import Client  # <-- new
from generate_copy_enhanced import generate_social_media_caption

load_dotenv()

HF_SPACE_REPO = os.environ.get(
    "HF_SPACE_REPO",
    "PeteHarris3001/SOCIAL-CAPTIONER"   # from your screenshot
)

def _call_hf_space(topic, platform, tone, trend):
    """
    Calls the Hugging Face Space using gradio_client.
    Matches the panel you saw: api_name="/predict"
    """
    try:
        client = Client(HF_SPACE_REPO)  # public Space needs no token
        # The param names below must match the panel in your screenshot
        result = client.predict(
            topic=topic or "",
            platform=(platform or "instagram"),
            tone=(tone or "engaging"),
            trend=(trend or ""),     # your UI marks it 'Required'—send "" if blank
            api_name="/predict"
        )
        # result is already the caption string
        if isinstance(result, str) and result.strip():
            return result.strip()
    except Exception as e:
        print(f"[hf] gradio_client error: {e}")
    return None

def generate_social_copy(prompt: str) -> str:
    # minimal parser in case your /api/content/generate still sends a prompt
    topic, platform, tone, trend = "", "instagram", "engaging", ""
    for line in (prompt or "").splitlines():
        lower = line.lower()
        if lower.startswith("topic:"):
            topic = line.split(":", 1)[1].strip()
        elif lower.startswith("platform:"):
            platform = (line.split(":", 1)[1].strip() or "instagram").lower()
        elif lower.startswith("tone:"):
            tone = (line.split(":", 1)[1].strip() or "engaging").lower()
        elif lower.startswith("trend:"):
            trend = line.split(":", 1)[1].strip()

    # Try the Space first
    cap = _call_hf_space(topic, platform, tone, trend)
    if cap:
        return cap

    # Fallback to your template so MVP still works
    tpl = generate_social_media_caption(topic or prompt, platform=platform, tone=tone, trend=trend)
    return (tpl["caption"] if isinstance(tpl, dict) else str(tpl)).strip()
