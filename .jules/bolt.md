# Bolt's Journal - Critical Learnings

## 2025-03-08 - Fast Metadata Endpoint and Playlist Overhead in yt-dlp
**Learning:** `yt_dlp.YoutubeDL.extract_info` defaults to parsing entire playlists when video URLs with `list=` parameters are provided, causing multi-second or timeout delays. Additionally, `/info` metadata extractions are I/O bound network calls (~1–3s).
**Action:** Always include `'noplaylist': True` in `yt_dlp` options for single video operations and use thread-safe in-memory caching (LRU/TTL) for media metadata endpoints.
