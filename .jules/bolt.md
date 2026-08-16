# Bolt's Journal

## 2026-08-16 - `yt_dlp` Playlist Overhead Optimization
**Learning:** `yt_dlp` extracts or downloads entire playlists by default when passed a video URL containing playlist parameters (`&list=...`). Setting `noplaylist: True` forces `yt_dlp` to extract/download only the target video, reducing network operations and execution time from O(N) playlist items to O(1).
**Action:** Always include `'noplaylist': True` in `yt_dlp.YoutubeDL` options when targeting single video/audio clips.
