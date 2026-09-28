## 2024-09-28 - Cache yt_dlp Video Metadata Extraction
**Learning:** `yt_dlp.extract_info` performs blocking network I/O that takes ~1-3s per request even with `skip_download=True`. Caching metadata results with an LRU cache (`@functools.lru_cache`) reduces latency for repeated metadata queries to <1ms.
**Action:** Always wrap `yt_dlp.extract_info` in a memoized helper for endpoints that fetch video metadata without downloading.
