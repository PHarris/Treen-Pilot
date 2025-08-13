# main.py
import os, base64, io
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Your modules
from content_generator import generate_social_copy
from generate_copy_enhanced import generate_social_media_caption

load_dotenv()

app = Flask(__name__)

# --- CORS: allow your Netlify origin (or * for quick test) ---
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")
CORS(
    app,
    resources={r"/api/*": {"origins": CORS_ORIGINS}},
    methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
    supports_credentials=False,
)

@app.get("/health")
def health():
    return jsonify({"ok": True, "env": {"CORS_ORIGINS": CORS_ORIGINS[:3]}})

# --- Helpers ---
def _safe_get_json(req):
    try:
        return req.get_json(force=True) or {}
    except Exception as e:
        print(f"[api] JSON parse error: {e}")
        return {}

def _make_hashtags_from_keywords(keywords):
    # very simple fallback
    tags = []
    for k in (keywords or []):
        k = "".join(ch for ch in k if ch.isalnum() or ch == " ").strip()
        if not k:
            continue
        tag = "#" + k.replace(" ", "")
        if tag not in tags:
            tags.append(tag)
    return " ".join(tags[:12])

# --- Generate copy (caption + hashtags + keywords) ---
@app.post("/api/content/generate")
def api_generate_content():
    payload = _safe_get_json(request)
    topic = payload.get("topic", "").strip()
    platform = payload.get("platform", "instagram").strip().lower()
    tone = payload.get("tone", "engaging").strip().lower()
    trend = payload.get("trend", "")

    if not topic:
        return jsonify({"error": "Missing field: topic"}), 400

    try:
        # 1) Primary: use your OpenAI-based generator (returns caption string)
        prompt = f"Topic: {topic}\nPlatform: {platform}\nTone: {tone}\nTrend: {trend}"
        caption = (generate_social_copy(prompt) or "").strip()

        # 2) Use your enhanced template to propose hashtags/keywords (safe even without API key)
        template = generate_social_media_caption(topic, platform=platform, tone=tone, trend=trend)
        # template is expected to be a dict; keep it safe:
        if isinstance(template, dict):
            t_caption = template.get("caption", "").strip()
            hashtags = template.get("hashtags", "")
            keywords = template.get("keywords", [])
            # Prefer AI caption if it returned something, otherwise template caption
            if not caption:
                caption = t_caption
        else:
            hashtags = ""
            keywords = []

        # Fallback tags if none
        if not hashtags:
            hashtags = _make_hashtags_from_keywords(keywords or [topic, tone, trend])

        resp = {
            "caption": caption or f"{topic} — {tone.title()}",
            "hashtags": hashtags,
            "keywords": keywords or [topic],
            "recommended_asset": None  # reserved for Phase 2 (DAM)
        }
        return jsonify(resp), 200

    except Exception as e:
        print(f"[api] /api/content/generate error: {e}")
        # Final fallback so frontend still renders
        resp = {
            "caption": f"{topic} — {tone.title()}",
            "hashtags": _make_hashtags_from_keywords([topic, tone, trend]),
            "keywords": [topic, tone],
            "recommended_asset": None
        }
        return jsonify(resp), 200

# --- Generate image ---
@app.post("/api/content/generate_image")
def api_generate_image():
    """
    Returns base64 PNG. Uses placeholder if no OPENAI_API_KEY or any error.
    """
    data = _safe_get_json(request)
    topic = data.get("topic", "")
    tone = data.get("tone", "")
    caption = data.get("caption", "")
    size = data.get("size", "1024x1024")

    # Try OpenAI images if key exists
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=key)
            resp = client.images.generate(
                model="gpt-image-1",
                prompt=f"{topic}. Tone: {tone}. Caption: {caption}",
                size=size,
                response_format="b64_json",
            )
            b64 = resp.data[0].b64_json
            return jsonify({"image_base64": b64, "mime": "image/png", "fallback": False}), 200
        except Exception as e:
            print(f"[api] OpenAI image error: {e}")

    # Placeholder PNG (simple gray)
    import PIL.Image as Image
    import PIL.ImageDraw as ImageDraw
    img = Image.new("RGB", (1024, 1024), (240, 240, 240))
    d = ImageDraw.Draw(img)
    d.text((40, 40), "Placeholder image\n(no OPENAI_API_KEY)", fill=(60, 60, 60))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return jsonify({"image_base64": b64, "mime": "image/png", "fallback": True}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
