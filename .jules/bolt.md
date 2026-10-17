## 2026-10-17 - Video Metadata Extraction Caching and Playlist Bypassing

**Learning:** `yt-dlp` metadata extraction (`extract_info`) is a network-bound blocking operation taking 0.5s–3s per call. Without `noplaylist: True`, URLs containing `&list=` query parameters cause `yt-dlp` to fetch metadata for all items in a playlist, drastically increasing response times. Caching video metadata responses with an LRU cache (`@functools.lru_cache`) eliminates repeated network overhead for duplicate requests (reducing latency to <0.01ms).

**Action:** Always include `noplaylist: True` in `yt-dlp` options for single video operations, and cache metadata extraction using `functools.lru_cache` when handling idempotent video information queries.
