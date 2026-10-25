# Bolt's Journal ⚡

## 2024-05-20 - Cache metadata and disable playlist extractions in yt-dlp

**Learning:** Extracting video info via `yt_dlp` involves network requests that add 1-3 seconds per call. Repeated requests for `/info` with the same URL can be cached with `functools.lru_cache` to respond instantly (<1ms). Additionally, video URLs containing `list=` params can trigger full playlist extraction unless `'noplaylist': True` is specified in `ydl_opts`.

**Action:** Always set `noplaylist: True` when processing single video URLs in `yt_dlp` and wrap expensive metadata extraction calls with `@lru_cache`.
