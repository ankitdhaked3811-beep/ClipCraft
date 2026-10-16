# Bolt's Journal - Critical Learnings

## 2025-05-18 - Caching yt-dlp Metadata Extraction
**Learning:** `yt_dlp.YoutubeDL.extract_info()` performs blocking external network calls taking 1-3+ seconds per invocation. In Flask web services providing video info previews, memoizing metadata extraction using `functools.lru_cache` reduces duplicate request latency to <1ms. Adding `noplaylist: True` in `ydl_opts` also avoids accidentally parsing entire playlist metadata when given video URLs with playlist params (`&list=...`).
**Action:** Wrap `yt_dlp` metadata lookups with `@lru_cache(maxsize=256)` and set `noplaylist: True` on single-video endpoints to save network I/O and CPU overhead.
