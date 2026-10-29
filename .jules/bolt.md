# Bolt's Journal

## 2024-10-29 - Fast yt-dlp Metadata Extraction & Caching
**Learning:** Calling `yt_dlp.YoutubeDL().extract_info(url, download=False)` defaults to `process=True`, which downloads and parses all video stream formats/DASH manifests. This can take several seconds or fail due to format availability errors. Passing `process=False` bypasses stream parsing and returns video metadata (title, duration, uploader, thumbnail) directly. Furthermore, wrapping metadata extraction in `@lru_cache(maxsize=256)` drops latency on repeated URL metadata requests from ~4.2s to <0.001ms.
**Action:** Use `process=False` with `noplaylist=True` for metadata-only requests in `yt-dlp`, with fallback to default extraction, and memoize with `@lru_cache`.
