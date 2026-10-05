## 2025-10-05 - Caching yt_dlp metadata & disabling playlist extraction
**Learning:** `yt_dlp.YoutubeDL.extract_info` performs slow network calls (~1-3s per request) and defaults to extracting full playlists when URLs contain playlist parameters (`&list=...`). Caching metadata with `@lru_cache` and passing `'noplaylist': True` reduces redundant metadata fetch times from ~1500ms to < 1ms (>99.9% faster).
**Action:** Always set `'noplaylist': True` in `yt_dlp` options for single video operations and use `@lru_cache` on `yt_dlp` metadata extraction helper functions in Python backends.
