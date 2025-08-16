# content_generator.py
import os
from dotenv import load_dotenv
from gradio_client import Client
from generate_copy_enhanced import generate_social_media_caption
from paraphraser import paraphrase_caption  # <-- from paraphraser.py

load_dotenv()

# Point to your public HF Space repo (captioner)
HF_SPACE_REPO = os.environ.get(
    "HF_SPACE_REPO",
    "PeteHarris3001/SOCIAL-CAPTIONER"
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
    Calls the SOCIAL-CAPTIONER Space via gradio_client.
    api_name must match the Space (we set it to '/predict').
    Returns the caption string or None.
    """
    try:
        client = Client(HF_SPACE_REPO)  # public Space; no token needed
        result = client.predict(
            topic=topic or "",
            platform=(platform or "instagram"),
            tone=(tone or "engaging"),
            trend=(trend or ""),
            api_name="/predict",
        )
        if isinstance(result, str) and result.strip():
            return result.strip()
    except Exception as e:
        print(f"[hf] gradio_client error: {e}")
    return None

def generate_social_copy(prompt: str) -> str:
    """
    Pipeline:
      1) Parse prompt -> topic/platform/tone/trend
      2) Try HF caption Space (free)
      3) Paraphrase with SOCIAL-PARAPHRASER (free)
      4) Fallback to rule-based generator if Space fails
      5) Paraphrase the fallback too
    """
    topic, platform, tone, trend = _parse_prompt(prompt)

    # Try HF Space first
    cap = _call_hf_space(topic, platform, tone, trend)
    if cap:
        better = paraphrase_caption(cap, platform, tone, "")
        return (better or cap).strip()

    # Fallback so MVP always works
    tpl = generate_social_media_caption(
        topic or prompt, platform=platform, tone=tone, trend=trend
    )
    raw_caption = (tpl["caption"] if isinstance(tpl, dict) else str(tpl)).strip()

    better = paraphrase_caption(raw_caption, platform, tone, "")
    return (better or raw_caption).strip()
