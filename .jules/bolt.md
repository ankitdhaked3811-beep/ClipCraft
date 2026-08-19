## 2025-05-18 - Avoid redundant yt-dlp metadata extraction & playlist downloads
**Learning:** `yt_dlp.extract_info` without `noplaylist: True` parses entire playlists if playlist URL query parameters are present (`&list=...`), causing multi-second delays and high resource usage. Furthermore, repeated `/info` calls for the same media URL redundantly perform external network requests.
**Action:** Always set `'noplaylist': True` in `yt_dlp` options for single-item extraction/clipping, and use bounded LRU caching (`@lru_cache(maxsize=1000)`) for idempotent video metadata requests.
