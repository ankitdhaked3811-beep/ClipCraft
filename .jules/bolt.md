## 2025-05-18 - Video Metadata Caching & Playlist Opt-out
**Learning:** `yt_dlp.YoutubeDL.extract_info` is an I/O bound network operation taking 1-3 seconds per request. Video URLs with playlist parameters (`&list=...`) incur additional latency by parsing full playlist metadata unless explicitly disabled.
**Action:** Use `@lru_cache` to cache video metadata extractions across `/info` calls and always set `'noplaylist': True` in `ydl_opts` when downloading or fetching info for single video clips.
