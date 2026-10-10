## 2026-10-10 - Memoizing yt-dlp Metadata Extraction

**Learning:** `yt_dlp.extract_info` performs network requests and metadata parsing that can take 1-3 seconds per request. For web services where users check video details before clipping or where multiple users check popular URLs, `functools.lru_cache` on extracted metadata eliminates 100% of network latency on repeated requests (~1-3s -> ~0ms).
**Action:** Wrap metadata extraction calls in an LRU cache helper function returning serializable dictionaries.
