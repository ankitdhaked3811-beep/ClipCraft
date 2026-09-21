## 2025-05-20 - Caching Video Metadata in yt-dlp Flask API
**Learning:** External video metadata extraction via `yt-dlp` is network-bound and takes ~1-3s per request. Caching extracted metadata with `@lru_cache` reduces repeat request times to <1ms. Additionally, URLs containing `&list=` query params cause `yt_dlp` to extract entire playlists unless `noplaylist: True` is explicitly configured in `ydl_opts`.
**Action:** Always wrap `yt_dlp` metadata lookups with caching and specify `noplaylist: True` for single-clip processing.
