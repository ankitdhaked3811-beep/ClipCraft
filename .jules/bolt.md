## 2026-08-23 - Video Metadata LRU Caching with yt-dlp

**Learning:** Extracting video info with `yt-dlp` executes network I/O that takes 0.5s - 2.0s per request. Wrapping metadata extraction with `@functools.lru_cache` reduces repeat query latencies to < 0.1ms (near instantaneous).
**Action:** Use `lru_cache` for expensive read-only metadata lookups in web endpoints.
