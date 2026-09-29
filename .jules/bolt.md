## 2026-03-29 - Memoizing yt-dlp metadata extractions and disabling playlist processing

**Learning:** `yt_dlp.extract_info` performs blocking network requests to video host servers on every execution (taking 1-3 seconds). In addition, without `'noplaylist': True`, URLs containing playlist query parameters cause `yt_dlp` to parse metadata for all videos in the playlist.

**Action:** Wrap metadata lookups in `@lru_cache(maxsize=256)` to serve repeated info queries instantly (<1ms), and set `'noplaylist': True` in `ydl_opts` to prevent unwanted playlist parsing overhead.
