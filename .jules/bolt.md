## 2024-10-14 - yt-dlp Metadata Caching and Fragment Concurrency in Flask Services

**Learning:** `yt_dlp.YoutubeDL.extract_info` performs network calls that take 1-3 seconds per request to extract video metadata. When users preview video/audio metadata repeatedly or when multiple requests hit `/info`, this creates severe response latency. Caching metadata with `@lru_cache(maxsize=256)` reduces response time from ~2000ms to <1ms for cached URLs. Furthermore, setting `noplaylist: True` and `extract_flat: 'in_playlist'` prevents `yt_dlp` from recursively extracting metadata for entire playlists when a single video URL is passed. Setting `concurrent_fragment_downloads: 4` enables parallel downloading of video segments for range clips.

**Action:** Always wrap metadata extractions in an LRU or TTL cache and configure `noplaylist` / `extract_flat` for metadata preview routes in media downloader backend APIs.
