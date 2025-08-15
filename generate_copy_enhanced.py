# generate_copy_enhanced.py
from datetime import datetime

# Character/hashtag guidance by platform
PLATFORM_RULES = {
    "instagram": {"max_caption": 2200, "hashtags": 8, "linebreak": "\n\n", "cta": "Double-tap if you agree ❤️"},
    "tiktok":    {"max_caption": 2200, "hashtags": 6, "linebreak": "\n",   "cta": "Follow for more 🔥"},
    "facebook":  {"max_caption": 63206,"hashtags": 3, "linebreak": "\n\n", "cta": "Share your thoughts below 👇"},
    "x":         {"max_caption": 260,  "hashtags": 2, "linebreak": "  ",   "cta": "RT if you agree"},
}

# Hashtag hygiene
BANNED_TAGS = {
    "#followforfollow", "#likeforlike", "#instagood", "#photooftheday", "#love", "#cute",
    "#beautiful", "#happy", "#fashion", "#art", "#style", "#picoftheday"
}

def _slugify(tag: str):
    return "#" + "".join(ch for ch in tag.lower() if ch.isalnum())

def _make_hashtags(topic: str, trend: str, platform: str, limit: int):
    # seed list from topic/trend
    seeds = []
    for piece in (topic or "").split():
        if len(piece) >= 3:
            seeds.append(_slugify(piece))
    if trend:
        for piece in trend.split():
            if len(piece) >= 3:
                seeds.append(_slugify(piece))
    # de-dup + filter
    tags = []
    seen = set()
    for t in seeds:
        if t in BANNED_TAGS or t in seen:
            continue
        seen.add(t)
        tags.append(t)
        if len(tags) >= limit:
            break
    # add platform tag if room
    if len(tags) < limit and platform in {"instagram","tiktok","x","facebook"}:
        tags.append("#" + platform)
    return " ".join(tags)

def _tone_prefix(tone: str):
    tone = (tone or "").lower()
    return {
        "engaging": "🔥",
        "playful": "😄",
        "professional": "💼",
        "bold": "💥",
    }.get(tone, "✨")

def generate_social_media_caption(topic: str, platform: str, tone: str, trend: str):
    platform = (platform or "instagram").lower()
    tone = (tone or "engaging").lower()
    rules = PLATFORM_RULES.get(platform, PLATFORM_RULES["instagram"])
    bullet = rules["linebreak"]

    # Headline + body
    prefix = _tone_prefix(tone)
    headline = f"{prefix} {topic.strip().capitalize()}"
    if trend:
        headline += f" • {trend.strip()}"

    # light guidance/benefit + CTA
    body = [
        f"{headline}",
        f"Here’s what’s trending {datetime.now():%B} {datetime.now().year} — let’s talk!",
        rules["cta"]
    ]
    caption = bullet.join(body)

    # trim for X
    if platform == "x" and len(caption) > rules["max_caption"]:
        caption = caption[: rules["max_caption"] - 1] + "…"

    hashtags = _make_hashtags(topic, trend, platform, rules["hashtags"])
    keywords = list(dict.fromkeys([topic.strip()] + ([trend.strip()] if trend else [])))[:3]

    return {
        "caption": caption,
        "hashtags": hashtags,
        "keywords": keywords,
        "recommended_asset": None,
    }
