## 2026-08-01 - Cache Video Metadata Requests to Avoid Network Latency

**Learning:** `yt_dlp.YoutubeDL.extract_info` performs synchronous HTTP requests to YouTube servers to extract video metadata. Caching this function with `functools.lru_cache` avoids redundant network latency (saving hundreds of milliseconds per repeated video URL query). Adding `noplaylist: True` to yt-dlp configuration also avoids fetching extra metadata when playlist links are provided.
**Action:** Wrap metadata fetching operations in `@lru_cache(maxsize=256)` and set `'noplaylist': True` in `yt_dlp` options for single video extraction endpoints.
