# Bolt's Journal - Critical Learnings

## 2026-08-01 - Caching `yt_dlp` metadata requests with LRU cache
**Learning:** Extracting video metadata with `yt_dlp` involves slow network calls to video platforms (~500ms+). Decorating a helper function with `functools.lru_cache` for URL metadata lookup avoids repeated network fetches for identical video URL queries, returning cached responses instantly (~0ms).
**Action:** Always wrap expensive, read-only metadata lookups like `yt_dlp.extract_info` in an LRU cache or key-value store when URLs are repeated across requests.
