## 2026-08-24 - yt-dlp Metadata Caching and Playlist Skipping

**Learning:** `yt_dlp.YoutubeDL.extract_info()` is network-bound and typically takes ~1-3 seconds per video URL. Adding thread-safe in-memory TTL caching for `/info` metadata requests eliminates redundant network requests for identical URLs (reducing cache-hit response time from >1000ms to <1ms). Additionally, explicitly setting `'noplaylist': True` in `ydl_opts` prevents `yt-dlp` from fetching playlist entries when single video URLs containing playlist parameters are parsed.
**Action:** Always pass `noplaylist: True` to `yt_dlp` options when clipping individual videos/audios, and cache `/info` responses using a thread-safe TTL cache.
