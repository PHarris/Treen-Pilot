# content_generator.py
import os, requests
from dotenv import load_dotenv
from generate_copy_enhanced import generate_social_media_caption

load_dotenv()

# Hardcoded Space URL (works even if the env var is missing)
HF_SPACE_URL = os.environ.get(
    "HF_SPACE_URL",
    "https://peteharris3001-social-captioner.hf.space"
)

def _parse_prompt(prompt: str):
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
    return topic, platform, tone, trend

def _call_hf_space(topic, platform, tone, trend):
    """
    Calls your Hugging Face Space's Gradio JSON endpoint.
    Expects: {"data": [topic, platform, tone, trend]}
    Returns: caption string or None.
    """
    url = HF_SPACE_URL.rstrip("/")
    if not url:
        return None
    try:
        payload = {"data": [topic, platform, tone, trend]}
        r = requests.post(f"{url}/run/predict", json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, dict) and "data" in data and data["data"]:
            return str(data["data"][0]).strip()
    except Exception as e:
        print(f"[hf] space call error: {e}")
    return None

def generate_social_copy(prompt: str) -> str:
    """
    Primary: use HF Space (free). Fallback: template generator (always works).
    """
    topic, platform, tone, trend = _parse_prompt(prompt)

    # 1) Try Space
    caption = _call_hf_space(topic, platform, tone, trend)
    if caption:
        return caption

    # 2) Fallback (keeps MVP running if Space is sleepy/down)
    tpl = generate_social_media_caption(topic or prompt, platform=platform, tone=tone, trend=trend)
    return (tpl["caption"] if isinstance(tpl, dict) else str(tpl)).strip()
