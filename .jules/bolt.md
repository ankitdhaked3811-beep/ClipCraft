# Bolt's Performance Journal

## 2024-10-21 - Cache yt-dlp Video Info & Prevent Playlist Processing
**Learning:** Extracting YouTube video metadata with `yt_dlp` is a network-heavy synchronous operation (~1.5–3s per request). Caching extracted video metadata with an LRU cache reduces duplicate lookup latencies from ~2000ms to <1ms. Additionally, setting `noplaylist: True` in `yt_dlp` options prevents accidental recursive extractions when URLs contain playlist IDs.
**Action:** Always cache immutable metadata lookups for external media APIs and set explicit options like `noplaylist: True` in `yt_dlp` to prevent slow recursive extractions.
