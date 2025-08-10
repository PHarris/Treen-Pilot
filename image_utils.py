import re
def build_image_prompt(topic: str, tone: str|None=None, caption: str|None=None, subject: str|None=None,
                       style: str|None=None, background: str|None=None, lighting: str|None=None,
                       color_palette: str|None=None):
    parts = []
    if subject: parts.append(f"Subject: {subject}.")
    else: parts.append(f"Subject inspired by: {topic}.")
    if style: parts.append(f"Style: {style}.")
    if background: parts.append(f"Background: {background}.")
    if lighting: parts.append(f"Lighting: {lighting}.")
    if color_palette: parts.append(f"Color palette: {color_palette}.")
    if tone: parts.append(f"Brand tone: {tone}.")
    if caption: parts.append(f"Caption context: {caption}.")
    parts.append("Social-media ready, clean composition, strong focal subject, high contrast, no embedded text.")
    prompt = " ".join(p.strip() for p in parts if p)
    prompt = re.sub(r"\s+", " ", prompt).strip()
    return prompt
