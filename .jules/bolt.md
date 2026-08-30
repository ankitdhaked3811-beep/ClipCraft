## 2025-08-30 - Cache `yt-dlp` Video Metadata Extractions
**Learning:** `yt_dlp.YoutubeDL.extract_info` performs synchronous HTTP requests to external media hosts which take several hundred milliseconds to seconds. Repeating metadata extractions for identical URLs severely impacts response latency.
**Action:** Use `functools.lru_cache` for video metadata extraction functions to instantly return cached info dicts on duplicate requests.
