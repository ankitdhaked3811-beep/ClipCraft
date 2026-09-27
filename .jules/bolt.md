# Bolt's Journal - Critical Learnings

## 2024-09-27 - LRU Caching for yt_dlp Video Info Extraction
**Learning:** In Flask services using `yt_dlp` for video metadata extraction (`extract_info`), external network calls to video platforms take 1-2+ seconds per request and can slow down metadata retrieval endpoints like `/info`. Caching `yt_dlp.extract_info` results with `@functools.lru_cache` and passing `'noplaylist': True` eliminates redundant external HTTP requests and playlist parsing on repeated queries, speeding up response times from ~1-2s to <1ms without requiring external dependencies or databases.
**Action:** Always wrap `yt_dlp` metadata extraction functions with `@lru_cache` and include `'noplaylist': True` in options when fetching single video information in microservices.
