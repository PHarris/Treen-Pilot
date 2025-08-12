# main.py
import os
import io
import base64

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load .env (safe if absent)
load_dotenv()

# ---- CORS setup ------------------------------------------------------------
# Set CORS_ORIGINS in secrets as a comma-separated list, e.g.
# "https://your-netlify-site.netlify.app,https://another.site"
_cors = os.getenv("CORS_ORIGINS", "*")
_CORS_ORIGINS = [o.strip() for o in _cors.split(",") if o.strip()] if _cors else ["*"]

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": _CORS_ORIGINS}})

# ---- Local modules ---------------------------------------------------------
from generate_copy_enhanced import (
    generate_social_media_caption,
    generate_social_media_hashtags,
    extract_key_words,
)
from match_assets import match_asset_to_copy
from image_utils import build_image_prompt
from google_trends_adapter import get_trending_terms


# ---- Optional OpenAI helpers -----------------------------------------------
def try_openai_text(topic: str, platform: str, tone: str, trend: str | None):
    """
    Returns a caption string if OpenAI is configured; otherwise None.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        # Lazy import so app still runs without openai installed
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        system_msg = (
            "Act as if you're the best social copywriter in the world. "
            "Write one concise, high-converting social caption. Keep under 220 words."
        )
        user_msg = (
            f"Platform: {platform}\n"
            f"Tone: {tone}\n"
            f"Topic: {topic}\n"
            f"Trend: {trend or ''}\n"
            "Constraints: No hashtags in the caption text. Friendly CTA at the end."
        )

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.8,
            max_tokens=220,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        print("OpenAI text error:", e)
        return None


def try_openai_image(prompt: str, size: str = "1024x1024"):
    """
    Returns base64-encoded PNG if OpenAI is configured; otherwise None.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        res = client.images.generate(model="gpt-image-1", prompt=prompt, size=size)
        return res.data[0].b64_json
    except Exception as e:
        print("OpenAI image error:", e)
        return None


# ---- Routes ----------------------------------------------------------------
@app.get("/")
def root():
    return (
        "TrendPilot API is running. Try:<br>"
        "<ul>"
        "<li><code>/health</code></li>"
        "<li><code>/api/trends?platform=instagram</code></li>"
        "<li><code>POST /api/content/generate</code></li>"
        "<li><code>POST /api/content/generate_image</code></li>"
        "</ul>"
    )


@app.get("/health")
def health():
    return jsonify({"ok": True, "service": "trendpilot-api", "cors": _CORS_ORIGINS})


@app.post("/api/content/generate")
def api_generate_content():
    """
    Body JSON:
      { topic, trend, platform, tone }
    """
    data = request.get_json(force=True) or {}
    topic = (data.get("topic") or "").strip()
    trend = (data.get("trend") or "").strip()
    platform = (data.get("platform") or "instagram").strip().lower()
    tone = (data.get("tone") or "engaging").strip()

    # 1) Try OpenAI for caption, else local generator
    caption = try_openai_text(topic, platform, tone, trend)
    if not caption:
        caption = generate_social_media_caption(topic, platform, tone, trend)

    # 2) Hashtags & keywords from local logic
    hashtags_list = generate_social_media_hashtags(topic, trend)
    hashtags = " ".join(hashtags_list)
    keywords = extract_key_words(f"{topic} {trend}".strip())

    # 3) Asset match from generated caption
    asset = match_asset_to_copy(caption)

    return jsonify(
        {
            "success": True,
            "caption": caption,
            "hashtags": hashtags,
            "keywords": keywords,
            "recommended_asset": asset,
        }
    )


@app.post("/api/content/generate_image")
def api_generate_image():
    """
    Body JSON:
      {
        topic, tone, caption, size="1024x1024",
        subject, style, background, lighting, color_palette
      }
    """
    data = request.get_json(force=True) or {}
    topic = (data.get("topic") or "").strip()
    tone = (data.get("tone") or "").strip()
    caption = (data.get("caption") or "").strip()
    size = (data.get("size") or "1024x1024").strip()

    # Optional structured fields
    subject = data.get("subject")
    style = data.get("style")
    background = data.get("background")
    lighting = data.get("lighting")
    color_palette = data.get("color_palette")

    # Build a good prompt for image gen
    prompt = build_image_prompt(
        topic=topic,
        tone=tone,
        caption=caption,
        subject=subject,
        style=style,
        background=background,
        lighting=lighting,
        color_palette=color_palette,
    )

    # Try OpenAI image; fallback to a simple generated PNG
    b64 = try_openai_image(prompt, size=size)
    if not b64:
        try:
            from PIL import Image, ImageDraw

            (w, h) = (1024, 1024) if size == "1024x1024" else (512, 512)
            img = Image.new("RGB", (w, h), (245, 248, 252))
            dr = ImageDraw.Draw(img)
            dr.rectangle((40, 40, w - 40, h - 40), outline=(46, 125, 255), width=8)
            preview = (topic or caption or "AI Image").strip()[:34]
            dr.text((60, h // 2 - 10), f"{preview}...", fill=(20, 23, 26))
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            return jsonify(
                {"success": True, "image_base64": b64, "mime": "image/png", "fallback": True}
            )
        except Exception as e:
            return jsonify({"success": False, "error": f"Could not generate image: {e}"}), 500

    return jsonify({"success": True, "image_base64": b64, "mime": "image/png"})


@app.get("/api/trends")
def api_trends():
    """
    Query params:
      platform (optional): instagram|facebook|tiktok|x|linkedin ...
    Uses google_trends_adapter.get_trending_terms with env defaults.
    """
    platform = (request.args.get("platform") or "instagram").strip().lower()
    geo = os.getenv("TRENDS_GEO", "GB")
    lang = os.getenv("TRENDS_LANG", "en-GB")
    ttl = int(os.getenv("TRENDS_TTL", "900"))

    terms = get_trending_terms(geo=geo, lang=lang, tz=0, ttl=ttl)
    shaped = terms[:20]

    # Simple shaping per platform (you can expand this later)
    if platform in ("tiktok", "x"):
        shaped = [("#" + t.replace(" ", "")) if not t.startswith("#") else t for t in shaped]

    return jsonify({"success": True, "platform": platform, "trends": shaped, "geo": geo})


# ---- Entrypoint ------------------------------------------------------------
if __name__ == "__main__":
    # Replit exposes the port; default to 5000 locally
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello, World!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)