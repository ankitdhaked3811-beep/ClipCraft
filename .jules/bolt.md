## 2025-09-10 - Cache Video Metadata with LRU Cache and Disable Playlists in yt-dlp
**Learning:** Extracting video metadata in `yt_dlp` triggers external network calls taking 500ms - 2000ms+ per request, and URL parameters with `list` cause `yt_dlp` to extract metadata for entire playlists.
**Action:** Use `@lru_cache(maxsize=256)` for metadata calls to return repeated requests instantly (~0ms), and set `'noplaylist': True` in `ydl_opts` to prevent unwanted playlist parsing.
