## 2025-05-18 - Cache YoutubeDL Metadata and Disable Playlist Parsing
**Learning:** `yt_dlp.YoutubeDL.extract_info` performs blocking network I/O to YouTube servers that can take 1.5s+ per call. When URLs contain list parameters (`&list=...`), yt-dlp defaults to extracting metadata for every video in the playlist, escalating response times to 20s+.
**Action:** Always set `'noplaylist': True` in `ydl_opts` when extracting metadata for individual clips, and wrap `get_video_metadata` calls in `@lru_cache(maxsize=256)` to serve repeated info requests instantly (<1ms).
