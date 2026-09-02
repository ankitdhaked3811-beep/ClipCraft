## 2026-08-01 - LRU Caching for yt_dlp Video Metadata
**Learning:** Extracting metadata via `yt_dlp.extract_info` performs blocking HTTP requests that take 500ms to 1500ms per call. Caching responses using `@lru_cache(maxsize=256)` drops latency to <1ms for repeated requests.
**Action:** Use memory caching (`@lru_cache`) for idempotent external metadata requests in Flask endpoints.
