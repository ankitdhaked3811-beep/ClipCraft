from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import tempfile
import os
import shutil
import threading
import time

app = Flask(__name__)
CORS(app)

# Store temp files and auto-delete after 1 hour
temp_files = {}

# Performance optimization: In-memory TTL cache for video info metadata with size limit.
# Prevents expensive network fetches with yt_dlp for identical video URLs.
# Expected impact: Reduces repeat /info response times from ~1-3s to <1ms (near instantaneous).
INFO_CACHE = {}
CACHE_TTL = 3600  # Cache duration in seconds (1 hour)
MAX_CACHE_SIZE = 1000
cache_lock = threading.Lock()

def get_cached_info(url):
    now = time.time()
    with cache_lock:
        if url in INFO_CACHE:
            cached_data, timestamp = INFO_CACHE[url]
            if now - timestamp < CACHE_TTL:
                return cached_data
            else:
                del INFO_CACHE[url]
    return None

def set_cached_info(url, data):
    now = time.time()
    with cache_lock:
        # Evict expired items if cache grows large
        if len(INFO_CACHE) >= MAX_CACHE_SIZE:
            expired_keys = [k for k, (v, ts) in INFO_CACHE.items() if now - ts >= CACHE_TTL]
            for k in expired_keys:
                del INFO_CACHE[k]
            # If still full, pop the oldest item
            if len(INFO_CACHE) >= MAX_CACHE_SIZE:
                oldest_key = min(INFO_CACHE.keys(), key=lambda k: INFO_CACHE[k][1])
                del INFO_CACHE[oldest_key]
        INFO_CACHE[url] = (data, now)

def cleanup_file(path, delay=3600, tmpdir=None):
    def _delete():
        time.sleep(delay)
        try:
            if os.path.exists(path):
                os.remove(path)
            temp_files.pop(path, None)
            # Performance/Resource optimization: Clean up temporary directory to prevent disk leaks
            if tmpdir and os.path.exists(tmpdir):
                shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass
    threading.Thread(target=_delete, daemon=True).start()

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

@app.route('/info', methods=['POST'])
def get_info():
    data = request.json or {}
    url = data.get('url')
    if not url:
        return jsonify({'error': 'URL required'}), 400

    # Optimization: Serve from cache if available
    cached_info = get_cached_info(url)
    if cached_info:
        return jsonify(cached_info)

    try:
        # Performance optimization: 'noplaylist': True prevents yt_dlp from downloading
        # playlist metadata when the URL contains a playlist parameter (&list=...).
        ydl_opts = {'quiet': True, 'no_warnings': True, 'skip_download': True, 'noplaylist': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        result = {
            'title': info.get('title', ''),
            'duration': info.get('duration', 0),
            'channel': info.get('uploader', ''),
            'thumbnail': info.get('thumbnail', ''),
        }
        set_cached_info(url, result)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/clip', methods=['POST'])
def create_clip():
    data = request.json or {}
    url = data.get('url')
    start = float(data.get('start', 0))
    end = float(data.get('end', 60))
    format_type = data.get('format_type', 'video')
    quality = data.get('quality', '720p')

    if not url:
        return jsonify({'error': 'URL required'}), 400
    if end - start > 185:
        return jsonify({'error': 'Max 3 minutes allowed'}), 400

    duration = end - start
    quality_map = {'1080p': '1080', '720p': '720', '480p': '480', '360p': '360'}
    q = quality_map.get(quality, '720')

    tmpdir = tempfile.mkdtemp()
    ext = 'mp3' if format_type == 'audio' else 'mp4'
    out_path = os.path.join(tmpdir, f'clip.{ext}')

    try:
        if format_type == 'audio':
            audio_quality = '320' if quality == '320kbps' else '128'
            # Performance optimization: 'noplaylist': True prevents playlist traversal
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(tmpdir, 'clip.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': audio_quality,
                }],
                'download_ranges': yt_dlp.utils.download_range_func(None, [(start, end)]),
                'force_keyframes_at_cuts': True,
                'quiet': True,
                'noplaylist': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            # find the mp3
            for f in os.listdir(tmpdir):
                if f.endswith('.mp3'):
                    out_path = os.path.join(tmpdir, f)
                    break
        else:
            # Performance optimization: 'noplaylist': True prevents playlist traversal
            ydl_opts = {
                'format': f'bestvideo[height<={q}]+bestaudio/best[height<={q}]',
                'outtmpl': out_path,
                'merge_output_format': 'mp4',
                'download_ranges': yt_dlp.utils.download_range_func(None, [(start, end)]),
                'force_keyframes_at_cuts': True,
                'quiet': True,
                'noplaylist': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        if not os.path.exists(out_path):
            shutil.rmtree(tmpdir, ignore_errors=True)
            return jsonify({'error': 'Download failed'}), 500

        temp_files[out_path] = True
        cleanup_file(out_path, tmpdir=tmpdir)

        return send_file(
            out_path,
            as_attachment=True,
            download_name=f'clip_{int(start)}_{int(end)}.{ext}',
            mimetype='audio/mpeg' if ext == 'mp3' else 'video/mp4'
        )

    except Exception as e:
        shutil.rmtree(tmpdir, ignore_errors=True)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
