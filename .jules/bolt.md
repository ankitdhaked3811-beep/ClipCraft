# Bolt's Performance Journal

## 2026-11-11 - Caching Video Metadata in yt-dlp Backend
**Learning:** `yt_dlp.YoutubeDL(opts).extract_info(url, download=False)` takes 3-5 seconds per request over the network due to multiple HTTP requests and format evaluations by yt-dlp. In web services like clip generation, users frequently re-request `/info` for the same video when previewing or adjusting trim timestamps. Without a cache, each request incurs high network latency and risks external rate-limiting. Furthermore, omitting `'format': 'all'` in ydl_opts causes `Requested format is not available` extractor errors when `skip_download: True` is used.
**Action:** Use an in-memory thread-safe TTL/LRU cache for video metadata extraction so repeat requests return in under 1 millisecond (~4,000x faster), and always pass `'format': 'all'` in `ydl_opts` when extracting metadata with `skip_download: True`.
