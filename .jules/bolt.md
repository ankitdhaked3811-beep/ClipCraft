## 2026-08-20 - LRU Caching and `noplaylist` Option for yt-dlp Metadata Extraction

**Learning:** `yt_dlp.extract_info()` is network-heavy (~1-2 seconds per request). Fetching metadata for identical URLs repeatedly blocks Flask worker threads. Furthermore, passing video URLs containing `&list=...` forces yt-dlp to inspect playlist items unless `noplaylist: True` is configured. Wrapping `extract_info` with `functools.lru_cache` reduces cached `/info` response times to < 1ms (~100% reduction in latency for duplicate queries).

**Action:** Always cache video metadata lookups in yt-dlp web wrappers and specify `noplaylist: True` for single-video info endpoints.
