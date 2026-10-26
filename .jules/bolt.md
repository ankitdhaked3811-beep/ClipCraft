# Bolt's Journal - Critical Learnings

## 2026-08-01 - Optimizing yt-dlp Metadata Extraction with Flat Extraction
**Learning:** Using `extract_flat: 'in_playlist'` in `yt-dlp.YoutubeDL` options avoids downloading full format definitions and webpage contents when fetching basic video/playlist metadata in `/info`. This significantly speeds up response times and lowers memory/bandwidth usage.
**Action:** Always set `extract_flat: 'in_playlist'` (or `True` depending on extractor) when only basic metadata (title, duration, thumbnail, uploader) is needed without downloading video formats.
