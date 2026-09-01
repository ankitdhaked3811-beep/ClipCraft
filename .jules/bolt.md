# Bolt Journal - Performance Learnings

## 2026-09-01 - Caching External Video Metadata in yt-dlp
**Learning:** Network calls to `yt_dlp.extract_info` take ~1.0s to 2.0s per request. Adding `@functools.lru_cache` for metadata queries reduces repeated response latency from ~1.0s to ~0ms, while adding `noplaylist` and `extract_flat: 'in_playlist'` speeds up uncached requests by ~45%.
**Action:** Always cache external web video metadata calls using LRU caching and pass `noplaylist` / `extract_flat` options when downloading is skipped.
