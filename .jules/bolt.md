## 2025-05-18 - Video Metadata Caching with LRU Cache
**Learning:** `yt_dlp.extract_info` performs blocking network requests that add 1000-3000ms latency to endpoint responses. Adding `@lru_cache(maxsize=256)` on helper extraction functions reduces redundant metadata requests to <1ms latency and prevents unnecessary network calls.
**Action:** Always wrap heavy, idempotent external network metadata extractions in LRU caching with sensible `maxsize` bounds.
