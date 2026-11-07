# Bolt's Performance Journal

## 2026-08-01 - Temporary Directory & Inode Exhaustion in Video Processing
**Learning:** `yt-dlp` creates auxiliary artifacts (fragments, temporary part files, merged audio/video files) inside the working directory. Only removing the single output file after a delay leaves orphaned directories and intermediate part files on disk, rapidly exhausting ephemeral container storage and inodes under high request volume or aborted downloads.
**Action:** Always clean up the entire temporary working directory (`shutil.rmtree`) both in scheduled delayed background cleanup and immediately upon download or processing failures.
