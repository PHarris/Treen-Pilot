# TrendPilot Backend (Replit/Railway) — GB default + Locked CORS

## Env
- `CORS_ORIGINS` — comma-separated allowed origins (no spaces). Example:
  `https://dashing-kringle-23c82d.netlify.app`
- `TRENDS_GEO=GB` (default), `TRENDS_LANG=en-GB`, `TRENDS_TTL=900`
- `OPENAI_API_KEY` (optional)

## Deploy (iPhone-friendly)
1) Create Python Repl → upload this ZIP → `pip install -r requirements.txt`
2) Set secrets: `CORS_ORIGINS`, `TRENDS_GEO`, `OPENAI_API_KEY` (optional)
3) Run → copy public URL → test `/health`

## Notes
- CORS is locked to the origins you provide; browsers from other sites will be blocked.
- Trends use Google Trends via `pytrends` and cache for TTL seconds.
