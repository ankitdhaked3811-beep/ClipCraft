## 2025-05-18 - `yt_dlp` Metadata Extraction Bottleneck
**Learning:** Calling `yt_dlp.extract_info` on every request to `/info` causes 1-3s latency per request due to network round-trips. Furthermore, URLs with `&list=` query parameters force `yt_dlp` to parse entire playlists unless `'noplaylist': True` is specified.
**Action:** Wrap metadata extraction functions with `functools.lru_cache` and always set `'noplaylist': True` in `ydl_opts` for single video operations.
