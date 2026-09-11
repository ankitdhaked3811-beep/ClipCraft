## 2025-05-18 - Caching yt-dlp Video Metadata Extraction in Flask Endpoints
**Learning:** Extracting video info with `yt_dlp` incurs network calls that take ~1.5s per request. Additionally, URLs containing playlist parameters cause yt-dlp to parse entire playlists unless `'noplaylist': True` is explicitly configured in `ydl_opts`.
**Action:** Use `@functools.lru_cache` for repeated metadata extractions and enforce `'noplaylist': True` on single-item extraction routes to keep response times under 1ms on cache hits and avoid unwanted playlist processing.
