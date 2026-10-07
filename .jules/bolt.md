## 2025-05-18 - Video Metadata LRU Caching
**Learning:** `yt_dlp` metadata extraction (`extract_info`) makes network requests taking ~500-1500ms per call. Since video title, duration, uploader, and thumbnail for a specific URL rarely change, wrapping the metadata extraction in an LRU cache (`@functools.lru_cache(maxsize=256)`) turns repeated `/info` calls into sub-millisecond memory lookups.
**Action:** When working with external media extractors like `yt_dlp` or standard HTTP scrapers, always cache metadata calls by URL key to prevent redundant network I/O.
