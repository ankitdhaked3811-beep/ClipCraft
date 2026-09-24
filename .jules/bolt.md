# Bolt's Journal - Critical Learnings

## 2026-08-01 - Avoid Full Playlist Metadata Extraction in yt-dlp
**Learning:** By default, when yt-dlp processes video URLs that contain playlist query parameters (e.g., `&list=PL...`), it fetches metadata for all videos in the playlist unless `noplaylist: True` option is explicitly set. This causes significant latency overhead when only single video metadata is needed.
**Action:** Always set `'noplaylist': True` in `ydl_opts` when extracting single video info in backend API endpoints.
