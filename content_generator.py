# content_generator.py
import os
from dotenv import load_dotenv
from openai import OpenAI
from generate_copy_enhanced import generate_social_media_caption

load_dotenv()

def generate_social_copy(prompt: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # fallback to your template generator using the whole prompt as topic
        return generate_social_media_caption(prompt, platform="instagram", tone="engaging", trend="")
    try:
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Act as if you're the best social copywriter in the world."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.8,
            max_tokens=220,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return generate_social_media_caption(prompt, platform="instagram", tone="engaging", trend="")
