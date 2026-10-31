# Bolt's Performance Journal

## 2026-08-01 - yt-dlp Extractor Initialization & Info Extraction Overhead
**Learning:** `yt_dlp.YoutubeDL()` initialization incurs ~150-200ms latency overhead on every invocation because it dynamically registers over 1,800 extractors. When combined with remote video metadata extraction over the network (~500ms-2s), querying `/info` for identical URLs is a significant bottleneck.
**Action:** Use memoization (e.g., `@functools.lru_cache`) on metadata extraction helper functions so repeated queries return immediately (<0.01ms), eliminating both extractor initialization cost and redundant network requests.
