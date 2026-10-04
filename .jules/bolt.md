# Bolt's Journal

## 2025-05-18 - Video Info Metadata Caching with lru_cache
**Learning:** Extracting video info with `yt-dlp` executes network calls that typically take 500ms to 2000ms per call. Since metadata endpoints for identical URLs are frequent in video clipping apps, memoizing metadata fetch results with `@lru_cache(maxsize=256)` drops repeat lookup response times down to < 1ms.
**Action:** Always wrap expensive external metadata extraction functions with memory caching when the return payload is deterministic for a given URL input.
