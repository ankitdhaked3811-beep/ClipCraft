# Bolt's Journal - Critical Learnings

## 2026-10-21 - LRU Caching for yt_dlp Video Metadata Extraction
**Learning:** `yt_dlp.YoutubeDL.extract_info(url, download=False)` performs synchronous network fetches and scraping, taking 1.0s - 1.5s per request. In a video processing/clipping service, clients frequently preview video metadata multiple times or hit `/info` before `/clip`. Wrapping metadata extraction with `functools.lru_cache(maxsize=256)` drops repeat response time to ~0.001s (~1000x faster).
**Action:** Always cache remote metadata lookups when inputs are deterministic URLs and metadata changes infrequently.
