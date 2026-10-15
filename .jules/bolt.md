## 2024-05-20 - Memoizing yt-dlp Metadata Extractions

**Learning:** `yt-dlp.YoutubeDL.extract_info()` performs synchronous HTTP network calls to fetch video metadata, taking ~1-3 seconds per invocation. For video clipping services where users frequently check info for popular/trending video URLs multiple times, un-cached calls introduce latency and hit external API rate limits. Memoizing `fetch_video_info` using `functools.lru_cache(maxsize=128)` turns repeated ~1-3s network calls into sub-millisecond memory lookups. In addition, using `noplaylist=True` prevents fetching metadata for entire playlists when a single video URL is provided.

**Action:** Wrap network-heavy extraction calls with `functools.lru_cache` for pure or idempotent inputs (like video URLs), ensuring `cache_clear()` is exposed or called in unit tests to maintain isolation.
