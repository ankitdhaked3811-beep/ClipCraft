## 2025-05-20 - yt-dlp single item extraction and disk leaks

**Learning:** When using `yt_dlp` to fetch metadata or download clips from user-provided URLs, omitting `'noplaylist': True` causes `yt_dlp` to parse and process every item in a playlist if the URL contains a `list=` parameter. Furthermore, temporary download files and directories created by `tempfile.mkdtemp()` leak on disk if only individual files are deleted with `os.remove()` rather than cleaning up the entire temporary directory with `shutil.rmtree()`.

**Action:** Always set `'noplaylist': True` in `yt_dlp` options for single video/audio extraction endpoints and clean up entire temporary directory paths using `shutil.rmtree()` upon expiration.
