## 2025-08-17 - LRU Caching for Video Metadata Extraction in Flask Backend
**Learning:** Video metadata extraction with `yt-dlp` involves costly network requests to YouTube/external servers that take several seconds. Caching metadata with `functools.lru_cache` reduces redundant lookups for identical video URLs to <1ms.
**Action:** Use `lru_cache` wrapper functions for idempotent network calls like metadata extraction in web applications.
