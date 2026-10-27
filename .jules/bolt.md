## 2026-08-01 - Cache Video Metadata Extraction with LRU Cache

**Learning:** Extracting video info with `yt-dlp` makes network calls that take 1-3 seconds per request. Adding `@lru_cache(maxsize=256)` on metadata extraction reduces repeated request latency from ~1000ms+ down to <1ms without requiring external dependencies or services like Redis. Additionally, setting `'noplaylist': True` in `yt-dlp` options prevents unnecessary overhead when URLs contain playlist parameters.
**Action:** Always wrap expensive external metadata extractions (such as `yt-dlp.extract_info`) with in-memory caching for repeated lookups.
