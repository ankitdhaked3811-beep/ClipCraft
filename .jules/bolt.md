## 2024-10-11 - Cache yt_dlp Video Metadata Extraction in Web API

**Learning:** `yt_dlp.YoutubeDL.extract_info` performs blocking network I/O and HTML/JS parsing when fetching video metadata, taking 1.5–3+ seconds per request. Wrapping metadata extraction in `@functools.lru_cache(maxsize=256)` and adding `'noplaylist': True` to `ydl_opts` eliminates redundant external requests for duplicate video URL queries, reducing cached `/info` response latency from ~2,000ms to <1ms.

**Action:** Always memoize / cache external media extractor calls (`yt_dlp`) and include `'noplaylist': True` when extracting single-item metadata to prevent unintended playlist traversal overhead.
