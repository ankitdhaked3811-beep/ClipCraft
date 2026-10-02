## 2025-05-18 - Caching yt-dlp Video Info Extraction
**Learning:** Video metadata queries using `yt-dlp.YoutubeDL.extract_info` involve external network HTTP requests and HTML/JSON parsing which can take anywhere from 500ms to 2000ms+ per request. In web applications like ClipCraft, users frequently query video details or re-query when tweaking parameters.
**Action:** Caching the resulting metadata dictionary with a TTL (e.g. 1 hour) and maximum size limit completely bypasses network overhead for duplicate requests, reducing response latency from ~1-2 seconds down to <1ms.
