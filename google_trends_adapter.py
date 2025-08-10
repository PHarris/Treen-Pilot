from datetime import datetime, timedelta
from typing import List
import os
from pytrends.request import TrendReq

_cache = { "key": None, "data": [], "expires": datetime.min }

def get_trending_terms(geo: str = "GB", lang: str = "en-GB", tz: int = 0, ttl: int = 900) -> List[str]:
    # cache key by geo/lang
    key = f"{geo}:{lang}"
    now = datetime.utcnow()
    if _cache["key"] == key and now < _cache["expires"]:
        return _cache["data"]
    try:
        pytrends = TrendReq(hl=lang, tz=tz)
        df = pytrends.trending_searches(pn='united_kingdom' if geo.upper()=='GB' else None)
        terms = []
        if df is not None and not df.empty:
            col = df.columns[0]
            terms = [str(x) for x in df[col].tolist() if isinstance(x, str)]
        # fallback if empty
        if not terms:
            terms = ["local events","breaking news","festival","premier league","back to school"]
        _cache["key"] = key
        _cache["data"] = terms[:20]
        _cache["expires"] = now + timedelta(seconds=ttl)
        return _cache["data"]
    except Exception:
        return ["local events","breaking news","festival","premier league","back to school"]
