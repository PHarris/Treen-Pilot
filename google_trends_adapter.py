from __future__ import annotations
from datetime import datetime, timedelta
from typing import List, Optional
import os
from pytrends.request import TrendReq

# Simple in-memory cache
_cache = {"key": None, "data": [], "expires": datetime.min}

# Map common GEO codes to pytrends "pn" country names
_PN_MAP = {
    "GB": "united_kingdom",
    "US": "united_states",
    "IE": "ireland",
    "CA": "canada",
    "AU": "australia",
    "NZ": "new_zealand",
    "DE": "germany",
    "FR": "france",
    "ES": "spain",
    "IT": "italy",
    "NL": "netherlands",
    "SE": "sweden",
    "NO": "norway",
    "DK": "denmark",
    "FI": "finland",
    "BE": "belgium",
    "CH": "switzerland",
    "AT": "austria",
    "PL": "poland",
    "PT": "portugal",
    "GR": "greece",
    # add more as needed
}

_FALLBACK = ["local events", "breaking news", "festival", "Premier League", "back to school"]

def get_trending_terms(
    geo: str = "GB",
    lang: str = "en-GB",
    tz: int = 0,
    ttl: int = 900
) -> List[str]:
    """
    Returns up to 20 trending search terms for the given country.
    Results are cached in-memory for `ttl` seconds to avoid rate limits.

    geo: ISO country code like "GB"
    lang: locale used by pytrends, e.g. "en-GB"
    tz: timezone offset in minutes; 0 is UTC
    """
    geo = (geo or "GB").upper()
    key = f"{geo}:{lang}"
    now = datetime.utcnow()

    # Serve from cache if valid
    if _cache["key"] == key and now < _cache["expires"]:
        return _cache["data"]

    try:
        pn = _PN_MAP.get(geo)
        pytrends = TrendReq(hl=lang, tz=tz)
        # If we have a country mapping, use it; else fall back to global "trending_searches()"
        if pn:
            df = pytrends.trending_searches(pn=pn)
        else:
            df = pytrends.trending_searches()  # global trending if no mapping

        terms: List[str] = []
        if df is not None and not df.empty:
            # The trending_searches DataFrame is a single column with rows of terms
            col = df.columns[0]
            terms = [str(x).strip() for x in df[col].tolist() if isinstance(x, str)]

        if not terms:
            terms = _FALLBACK

        # Cache and return top 20
        _cache["key"] = key
        _cache["data"] = terms[:20]
        _cache["expires"] = now + timedelta(seconds=max(60, int(ttl)))
        return _cache["data"]

    except Exception as e:
        # Log to console and return a safe fallback
        print(f"[trends] error: {e}")
        return _FALLBACK