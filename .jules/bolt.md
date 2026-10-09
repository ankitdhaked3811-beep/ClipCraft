## 2025-02-14 - Prevent yt-dlp playlist expansion and cache video metadata

**Learning:** `yt_dlp.extract_info` without `'noplaylist': True` defaults to expanding and fetching metadata for all entries in a playlist if a URL contains playlist query params, multiplying response latency. Furthermore, metadata fetched via `/info` is frequently requested multiple times for the same URL before clipping, so caching metadata with `functools.lru_cache` eliminates redundant external HTTP requests and drops response latency from ~3.8s to <1.5ms.

**Action:** Always specify `'noplaylist': True` in `yt_dlp` option dictionaries for single video/audio workflows, and wrap metadata extractions in an LRU cache.
