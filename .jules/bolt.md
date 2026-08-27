# Bolt's Journal - Critical Learnings

## 2026-08-01 - yt-dlp Metadata Extraction Optimization
**Learning:** `yt_dlp.YoutubeDL` by default parses full format details and playlist info when calling `extract_info`. Using `noplaylist: True` and `extract_flat: 'in_playlist'` speeds up metadata extraction for `/info` endpoint significantly by avoiding unnecessary resolution/playlist overhead.
**Action:** Include `noplaylist: True` and `extract_flat: 'in_playlist'` in `yt_dlp` options when fetching video metadata.
