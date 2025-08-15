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
    Calls the Hugging Face Space. Tries both Gradio API styles:
      - /run/predict  (Gradio 4+)
      - /api/predict  (Gradio 3)
    Returns caption text or None.
    """
    base = HF_SPACE_URL.rstrip("/") if HF_SPACE_URL else None
    if not base:
        return None

    payload = {"data": [topic, platform, tone, trend]}
    endpoints = [f"{base}/run/predict", f"{base}/api/predict"]  # try v4 then v3

    for url in endpoints:
        try:
            r = requests.post(url, json=payload, timeout=60)
            # Some Spaces return 200 with an error payload; enforce 2xx:
            r.raise_for_status()
            data = r.json()
            if isinstance(data, dict) and "data" in data and data["data"]:
                return str(data["data"][0]).strip()
        except Exception as e:
            print(f"[hf] try {url} -> {e}")

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
