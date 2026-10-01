# Bolt's Journal ⚡

## 2025-05-18 - Video Info Metadata Caching with `lru_cache`
**Learning:** Extracting video info with `yt-dlp` sends remote HTTP queries to video hosting servers, taking hundreds of milliseconds to several seconds per request. Wrapping extraction in `@lru_cache(maxsize=256)` drops duplicate request latency to < 1ms.
**Action:** Always check if network/I/O metadata extraction endpoints can be memoized/cached safely when request parameters are deterministic.
