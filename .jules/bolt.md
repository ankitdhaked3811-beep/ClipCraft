## 2026-08-26 - Fast video metadata extraction with flat extraction & LRU cache

**Learning:** `yt_dlp.YoutubeDL.extract_info(url, download=False)` defaults to downloading full video format trees, extracting all stream details and thumbnails, which takes ~4+ seconds per request and can fail on videos with restricted format formats. Setting `extract_flat: True` and `process=False` bypasses format processing, reducing extraction time drastically while preserving title, duration, uploader/channel, and thumbnail URL. Additionally, caching metadata with `@functools.lru_cache(maxsize=256)` makes subsequent requests to `/info` instantaneous (sub-millisecond).

**Action:** For video/audio metadata endpoints where full stream details are not needed, always use `extract_flat: True` and `process=False` alongside `@functools.lru_cache`.
