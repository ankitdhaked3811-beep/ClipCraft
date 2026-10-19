## 2026-03-29 - LRU Caching for Video Metadata Extraction
**Learning:** Video information extraction via `yt_dlp` involves network calls to YouTube/video platforms taking ~1-3s per request. Caching video metadata extraction results using standard library `functools.lru_cache` eliminates redundant network requests for duplicate URL lookups, reducing response latency to <1ms.
**Action:** Use `functools.lru_cache` for expensive read-only external API calls and metadata lookups that don't change frequently.
