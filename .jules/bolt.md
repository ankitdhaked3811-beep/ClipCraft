## 2025-09-03 - Caching yt-dlp Video Info Calls
**Learning:** Extracting video info via `yt_dlp.YoutubeDL.extract_info(url, download=False)` performs a full network fetch to the video host (e.g. YouTube API / web pages), taking ~1–3s per request.
**Action:** Implement an in-memory TTL cache for video metadata requests in lightweight web services to prevent redundant network latency and save bandwidth.
