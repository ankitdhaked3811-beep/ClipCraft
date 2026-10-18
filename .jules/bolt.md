## 2024-10-18 - Caching Remote Video Metadata and Disabling Playlist Processing in yt-dlp

**Learning:** Remote metadata extraction in media processing servers (e.g. `yt_dlp.YoutubeDL.extract_info`) is bottlenecked by network latency (1-3s per request). In addition, URLs containing playlist parameters (`&list=...`) default to extracting info for all playlist items unless `noplaylist: True` is configured.
**Action:** Always wrap `extract_info` calls for URL metadata endpoints with an in-memory LRU cache (`@lru_cache(maxsize=256)`) and ensure `'noplaylist': True` is included in `ydl_opts` to prevent redundant network roundtrips and unintended playlist expansion.
