from rapidfuzz import fuzz
MOCK_ASSETS = [
    { "filename": "eco_water_bottle.jpg", "tags": ["eco","sustainable","water","bottle"] },
    { "filename": "vegan_pasta_recipe.mp4", "tags": ["vegan","pasta","recipe","food","healthy"] },
    { "filename": "sunset_meditation.jpg", "tags": ["sunset","meditation","ocean","wellness"] },
    { "filename": "fitness_motivation.mp4", "tags": ["fitness","workout","exercise","motivation"] }
]
def _score_asset(asset, keywords: list) -> float:
    fields = (asset.get("tags", []) or []) + [asset.get("filename","")]
    best = 0.0
    for kw in keywords or []:
        for f in fields:
            best = max(best, fuzz.partial_ratio(kw.lower(), str(f).lower()))
    return best
def match_asset_to_copy(caption: str):
    kws = [w.strip("#.,!?:;").lower() for w in caption.split() if len(w) > 2]
    best = None; best_score = -1
    for a in MOCK_ASSETS:
        s = _score_asset(a, kws)
        if s > best_score: best, best_score = a, s
    if not best: return None
    return { **best, "score": round(float(best_score), 1) }
