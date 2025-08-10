import os, io, base64
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
load_dotenv()

# Read CORS origins from env (comma-separated, no spaces)
_cors = os.getenv("CORS_ORIGINS", "*")
origins = [o.strip() for o in _cors.split(",") if o.strip()] if _cors else ["*"]

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": origins}})

from generate_copy_enhanced import generate_social_media_caption, generate_social_media_hashtags, extract_key_words
from match_assets import match_asset_to_copy
from image_utils import build_image_prompt
from google_trends_adapter import get_trending_terms

def try_openai_text(topic, platform, tone, trend):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        sys = "Act as if you're the best social copywriter in the world. Write one concise, high-converting social caption. Keep under 220 words."
        user = f"Platform: {platform}\nTone: {tone}\nTopic: {topic}\nTrend: {trend or ''}\nConstraints: No hashtags in caption. Friendly CTA at end."
        resp = client.chat.completions.create(model="gpt-4o-mini",
            messages=[{"role":"system","content":sys},{"role":"user","content":user}],
            temperature=0.8, max_tokens=220)
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print("OpenAI text error:", e); return None

def try_openai_image(prompt, size="1024x1024"):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        res = client.images.generate(model="gpt-image-1", prompt=prompt, size=size)
        return res.data[0].b64_json
    except Exception as e:
        print("OpenAI image error:", e); return None

@app.get("/health")
def health(): 
    return {"ok": True, "service": "trendpilot-api", "cors": origins}

@app.post("/api/content/generate")
def generate_content():
    data = request.get_json(force=True) or {}
    topic = (data.get("topic") or "").strip()
    trend = (data.get("trend") or "").strip()
    platform = (data.get("platform") or "instagram").strip().lower()
    tone = (data.get("tone") or "engaging").strip()
    caption = try_openai_text(topic, platform, tone, trend) or generate_social_media_caption(topic, platform, tone, trend)
    hashtags = generate_social_media_hashtags(topic, trend)
    keywords = extract_key_words(f"{topic} {trend}")
    asset = match_asset_to_copy(caption)
    return jsonify({"success": True,"caption": caption,"hashtags": " ".join(hashtags),"keywords": keywords,"recommended_asset": asset})

@app.post("/api/content/generate_image")
def generate_image():
    data = request.get_json(force=True) or {}
    topic = (data.get("topic") or "").strip()
    tone = (data.get("tone") or "").strip()
    caption = (data.get("caption") or "").strip()
    size = data.get("size") or "1024x1024"
    subject = data.get("subject"); style = data.get("style"); background = data.get("background")
    lighting = data.get("lighting"); color_palette = data.get("color_palette")
    prompt = build_image_prompt(topic, tone, caption, subject, style, background, lighting, color_palette)
    b64 = try_openai_image(prompt, size=size)
    if not b64:
        try:
            from PIL import Image, ImageDraw
            (w, h) = (1024, 1024) if size == "1024x1024" else (512, 512)
            img = Image.new("RGB", (w, h), (245, 248, 252))
            dr = ImageDraw.Draw(img)
            dr.rectangle((40,40,w-40,h-40), outline=(46,125,255), width=8)
            dr.text((60, h//2 - 10), f"{topic[:30]}...", fill=(20,23,26))
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            return jsonify({"success": True, "image_base64": b64, "mime": "image/png", "fallback": True})
        except Exception as e:
            return jsonify({"success": False, "error": f"Could not generate image: {e}"}), 500
    return jsonify({"success": True, "image_base64": b64, "mime": "image/png"})

@app.get("/api/trends")
def api_trends():
    platform = (request.args.get("platform") or "instagram").lower()
    geo = os.getenv("TRENDS_GEO", "GB")
    lang = os.getenv("TRENDS_LANG", "en-GB")
    ttl = int(os.getenv("TRENDS_TTL", "900"))
    terms = get_trending_terms(geo=geo, lang=lang, tz=0, ttl=ttl)

    # Light shaping per platform (e.g., add hashtags for TikTok/X)
    shaped = terms[:20]
    if platform in ("tiktok","x"):
        shaped = [("#" + t.replace(" ", "")) if not t.startswith("#") else t for t in shaped]

    return jsonify({"success": True, "platform": platform, "trends": shaped, "geo": geo})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
