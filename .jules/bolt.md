## 2026-03-31 - Cache Metadata Extractions in Flask/yt-dlp Applications

**Learning:** `yt_dlp.extract_info` performs synchronous HTTP requests to fetch video metadata, introducing high latency (1-3s) on repeated queries for the same URL. Wrapping info extractions with `functools.lru_cache` and passing `'noplaylist': True` eliminates network roundtrips for previously fetched URLs and prevents parsing unwanted playlist metadata.

**Action:** Wrap `yt_dlp` metadata extraction helpers in `@functools.lru_cache(maxsize=...)` and set `'noplaylist': True` in `ydl_opts` when extracting video info.
