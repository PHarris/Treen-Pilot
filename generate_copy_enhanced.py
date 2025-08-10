import random, re
COMMON_WORDS = {'the','a','an','and','or','but','in','on','at','to','for','of','with','by','is','are','was','were','be','been','have','has','had','do','does','did','will','would','could','should','may','might','can','our','we','us','here','there','this','that','these','those','new','your','its','their'}
KEYWORD_CATEGORIES = {
    "eco": ["eco","green","sustainable","environment","planet","recycled","climate"],
    "food": ["food","recipe","cooking","delicious","vegan","healthy","pasta"],
    "fitness": ["fitness","workout","exercise","health","motivation","gym","training"],
    "tech": ["tech","technology","ai","innovation","digital","automation","software","platform"],
}
def extract_key_words(text: str) -> list:
    words = re.findall(r'\b\w+\b', (text or '').lower())
    uniq = []
    for w in words:
        if w not in COMMON_WORDS and len(w) > 2 and w not in uniq:
            uniq.append(w)
    return uniq[:8]
def matched_category(key_words):
    for cat, terms in KEYWORD_CATEGORIES.items():
        if any(t in key_words for t in terms):
            return cat
    return None
def _templates_for(tone: str, category: str|None):
    tone = (tone or "engaging").lower()
    if tone.startswith("engaging"):
        base = ["🚀 {topic} — let's make it happen!","✨ {topic}. Ready to try it?","🎉 {topic}! Join the conversation."]
        spec = {
            "eco": ["🌱 {topic} — small steps, big impact.","🌍 {topic}. Better for the planet, better for you."],
            "food":["🍝 {topic}. Crave-worthy and simple.","🍽️ {topic} — what are you cooking tonight?"],
            "fitness":["💪 {topic}. Let's go!","🏃 {topic}. One more rep."],
            "tech":["🤖 {topic}. The future is now.","💻 {topic} — smarter, faster, easier."]
        }
        return (spec.get(category, []) or base) + base
    if tone.startswith("professional"):
        return ["{topic} — driving measurable outcomes.","Explore {topic} and its impact on your KPIs.","{topic}: best practices and next steps."]
    if tone.startswith("humorous"):
        return ["{topic}? Bold move. I respect it. 😅","Breaking: {topic} now responsible for 99% of my productivity… or lack thereof.","{topic}. Because chaos needed a sidekick."]
    if tone.startswith("inspir"):
        return ["{topic} is a step toward your goals. Keep going. 💫","Let {topic} be the spark. 🌟","Every day is a chance to choose {topic}."]
    return ["{topic} — let's talk."]
def generate_social_media_caption(topic: str, platform: str = "instagram", tone: str = "engaging", trend: str|None=None) -> str:
    combo_text = topic or ""
    if trend: combo_text = f"{topic} • Trend: {trend}"
    keys = extract_key_words(combo_text)
    category = matched_category(keys)
    templates = _templates_for(tone, category)
    cap = random.choice(templates).format(topic=topic)
    if tone.lower().startswith("engaging"): cap += " Drop your thoughts below!"
    return cap
def generate_social_media_hashtags(topic: str, trend: str|None=None) -> list:
    keys = extract_key_words(f"{topic} {trend or ''}")
    return [f"#{k.capitalize()}" for k in keys[:5]]
