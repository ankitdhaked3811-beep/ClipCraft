# Bolt's Journal - Critical Learnings

## 2025-05-18 - `yt-dlp` Video Info Caching & Playlist Opt-out
**Learning:** `yt_dlp.extract_info()` performs external HTTP requests to YouTube/video providers, taking ~1-3s per call. Adding LRU caching (`@lru_cache(maxsize=256)`) eliminates redundant network latency for popular/repeated URLs. Setting `'noplaylist': True` prevents unnecessary extraction/traversal of entire playlist structures when URLs include playlist query params.
**Action:** Always set `'noplaylist': True` when single video extraction is intended in `yt-dlp`, and memoize video info lookups using `@lru_cache`.
