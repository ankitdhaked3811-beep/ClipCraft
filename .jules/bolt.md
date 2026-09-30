## 2025-05-18 - LRU Caching and Playlist Option for yt-dlp Video Metadata
**Learning:** `yt_dlp` network metadata extraction is an expensive network call (often 1-3+ seconds). Adding `@lru_cache(maxsize=256)` on video metadata lookups drastically lowers response time to <1ms for repeated URL queries. Additionally, passing `'noplaylist': True` prevents unwanted playlist processing when URLs contain playlist parameters.
**Action:** Always enforce `'noplaylist': True` and LRU caching for video info extraction endpoints using `yt_dlp` to prevent redundant network I/O.
