# paraphraser.py
import os
from gradio_client import Client

PARA_REPO = os.environ.get("HF_PARAPHRASER_REPO", "PeteHarris3001/SOCIAL-PARAPHRASER")

def paraphrase_caption(base_caption: str, platform: str, tone: str, hashtags: str = "") -> str | None:
    try:
        client = Client(PARA_REPO)
        result = client.predict(
            base_caption, platform or "instagram", tone or "engaging", hashtags or "",
            api_name="/predict"
        )
        if isinstance(result, str) and result.strip():
            return result.strip()
    except Exception as e:
        print(f"[hf-paraphraser] error: {e}")
    return None
