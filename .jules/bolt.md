# Bolt's Journal

## 2026-08-01 - Video Metadata Extraction Caching
**Learning:** `yt_dlp.YoutubeDL.extract_info` performs network requests and webpage parsing on every invocation, taking 1-3s per URL. For repeated queries on the same video URL (e.g. video preview/info endpoints), using `@functools.lru_cache` reduces latency from seconds to under 1 millisecond.
**Action:** Wrap `yt_dlp` metadata extractions with `@functools.lru_cache` for read-only metadata endpoints.
