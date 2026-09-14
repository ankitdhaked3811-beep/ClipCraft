## 2026-08-01 - Cache yt-dlp Metadata Extraction
**Learning:** `yt-dlp.extract_info` performs blocking network requests taking 1-3+ seconds per video URL. In Flask apps serving video metadata endpoints, LRU caching with `@lru_cache(maxsize=128)` and setting `noplaylist: True` in `ydl_opts` dramatically reduces response times from ~2000ms to <1ms for repeated URL queries while avoiding unnecessary playlist extractions.
**Action:** Always wrap external video/media metadata extraction functions with LRU caching and pass `noplaylist: True` when individual video metadata is required.
