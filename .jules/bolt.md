## 2025-05-18 - Metadata Extraction Caching & Playlist Bypassing
**Learning:** `yt_dlp.extract_info` performs external network calls (1-3s). Caching extracted video metadata with `@functools.lru_cache` makes repeated queries instant (<1ms). Setting `'noplaylist': True` in `ydl_opts` prevents `yt_dlp` from fetching full playlist metadata when URLs include playlist parameters.
**Action:** Always include `'noplaylist': True` for single-video clipping options in `yt_dlp` and cache video info responses for repeated requests.
