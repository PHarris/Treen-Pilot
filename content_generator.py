# content_generator.py
import os
import re
from dotenv import load_dotenv
from gradio_client import Client
from generate_copy_enhanced import generate_social_media_caption
from paraphraser import paraphrase_caption  # your existing helper

load_dotenv()

# Point to your public HF Space repo (captioner)
HF_SPACE_REPO = os.environ.get("HF_SPACE_REPO", "PeteHarris3001/SOCIAL-CAPTIONER").strip()

# -------------------------
# Helpers
# -------------------------
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

def _safe_hashtag(token: str) -> str:
    token = re.sub(r"[^A-Za-z0-9]", "", token or "")
    return f"#{token}" if token else ""

def _basic_hashtags(topic: str, trend: str, platform: str, limit: int = 8) -> str:
    """Very small backup in case generate_social_media_caption doesn't give hashtags."""
    tags = []
    for w in (topic or "").split():
        t = _safe_hashtag(w)
        if t and t not in tags:
            tags.append(t)
    for w in (trend or "").split():
        t = _safe_hashtag(w)
        if t and t not in tags:
            tags.append(t)
    if platform:
        t = _safe_hashtag(platform)
        if t and t not in tags:
            tags.append(t)
    return " ".join(tags[:limit])

def _call_hf_space(topic, platform, tone, trend, timeout_sec: int = 60) -> str | None:
    """
    Calls the SOCIAL-CAPTIONER Space via gradio_client.
    api_name must match the Space (we set it to '/predict').
    Returns a caption string or None.
    """
    try:
        client = Client(HF_SPACE_REPO)  # public Space; no token needed
        result = client.predict(
            topic=topic or "",
            platform=(platform or "instagram"),
            tone=(tone or "engaging"),
            trend=(trend or ""),
            api_name="/predict",
            timeout=timeout_sec,  # <— added timeout
        )
        if isinstance(result, str) and result.strip():
            return result.strip()
        print(f"[hf] Unexpected response type from {HF_SPACE_REPO}: {type(result)}")
    except Exception as e:
        print(f"[hf] gradio_client error calling {HF_SPACE_REPO}/predict: {e}")
    return None

def _build_response(final_caption: str, topic: str, platform: str, tone: str, trend: str) -> dict:
    """
    Ensure we always return the full JSON structure.
    Uses your rule engine to derive hashtags/keywords, but overwrites the caption
    with the (possibly paraphrased) final_caption.
    """
    try:
        base = generate_social_media_caption(topic or "", platform=platform, tone=tone, trend=trend)
        if isinstance(base, dict):
            hashtags = base.get("hashtags") or _basic_hashtags(topic, trend, platform)
            keywords = base.get("keywords") or ([topic] if topic else [])
        else:
            hashtags = _basic_hashtags(topic, trend, platform)
            keywords = ([topic] if topic else [])
    except Exception as e:
        print(f"[rules] generate_social_media_caption error: {e}")
        hashtags = _basic_hashtags(topic, trend, platform)
        keywords = ([topic] if topic else [])

    return {
        "caption": (final_caption or "").strip(),
        "hashtags": hashtags.strip() if isinstance(hashtags, str) else " ".join(hashtags or []),
        "keywords": [k for k in (keywords or []) if k],
        "recommended_asset": None,
    }

# -------------------------
# Public entry point
# -------------------------
def generate_social_copy(prompt: str) -> dict:
    """
    Pipeline:
      1) Parse prompt -> topic/platform/tone/trend
      2) Try HF caption Space (free)
      3) Paraphrase with SOCIAL-PARAPHRASER (free)
      4) Fallback to rule-based generator if Space fails
      5) Always return full JSON (caption/hashtags/keywords/recommended_asset)
    """
    topic, platform, tone, trend = _parse_prompt(prompt)

    # 1) Try HF Space first
    cap = _call_hf_space(topic, platform, tone, trend, timeout_sec=60)
    if cap:
        # 2) Paraphrase
        better = paraphrase_caption(cap, platform, tone, "")
        final_caption = (better or cap).strip()
        return _build_response(final_caption, topic, platform, tone, trend)

    # 3) Fallback so MVP always works (rules)
    try:
        tpl = generate_social_media_caption(topic or prompt, platform=platform, tone=tone, trend=trend)
        raw_caption = (tpl["caption"] if isinstance(tpl, dict) else str(tpl)).strip()
    except Exception as e:
        print(f"[rules] fallback caption error: {e}")
        raw_caption = (topic or prompt or "").strip()

    # 4) Paraphrase the fallback too
    better = paraphrase_caption(raw_caption, platform, tone, "")
    final_caption = (better or raw_caption).strip()

    # 5) Return full JSON
    return _build_response(final_caption, topic, platform, tone, trend)
