# Bolt's Performance Journal

This journal records critical learnings, surprising bottlenecks, and architectural insights discovered during performance optimization.

## 2026-08-01 - yt-dlp metadata extraction overhead and in-memory TTL caching
**Learning:** `yt_dlp.YoutubeDL(opts).extract_info(url, download=False)` involves initializing yt-dlp parsers and making network HTTP round-trips to the media provider, which takes ~100-200ms of parser setup and ~500ms-2s of network time per request. For repeated URL queries or frontend re-queries, this adds massive latency and risks third-party rate limits. An in-memory thread-safe TTL cache reduces response latency to <1ms.
**Action:** Always provide thread-safe caching for read-only external extraction calls like `/info`, and evict expired entries or bound maximum cache capacity to prevent memory bloat in constrained container environments (e.g. Render free tier).
