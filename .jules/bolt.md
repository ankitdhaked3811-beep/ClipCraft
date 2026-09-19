## 2025-05-18 - Prevent yt-dlp playlist scans & cache video metadata queries
**Learning:** Extracting video info with yt-dlp without `noplaylist: True` forces yt-dlp to fetch all playlist items if the URL contains playlist params (`&list=...`), turning a single metadata fetch into N network requests (10s+ latency). In addition, repeated calls to `/info` without caching hit external endpoints repeatedly.
**Action:** Always set `noplaylist: True` in `yt_dlp.YoutubeDL` options when targeting single videos, and cache metadata queries with `@lru_cache` for instant (<1ms) repeat responses.
