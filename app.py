from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import tempfile
import os
import threading
import time

app = Flask(__name__)
CORS(app)

# Store temp files and auto-delete after 1 hour
temp_files = {}

# Performance Optimization:
# In-memory TTL + LRU cache for video metadata requests on the /info endpoint.
# yt-dlp metadata extraction incurs significant network round-trips and CPU parsing (~500ms to 2000ms).
# Caching reduces response latency for repeated queries to < 1ms, saves egress bandwidth, and avoids rate limits.
INFO_CACHE_MAX_SIZE = 256
INFO_CACHE_TTL_SECONDS = 300  # 5 minutes cache TTL
info_cache = {}
info_cache_lock = threading.Lock()

def get_cached_info(url):
    """Retrieve video metadata from cache if present and not expired."""
    now = time.time()
    with info_cache_lock:
        if url in info_cache:
            entry = info_cache[url]
            if now < entry['expires_at']:
                # Re-insert to mark as recently used in LRU order
                info_cache[url] = info_cache.pop(url)
                return entry['data']
            else:
                del info_cache[url]
    return None

def set_cached_info(url, data):
    """Store video metadata into cache with TTL and evict oldest when capacity reached."""
    now = time.time()
    with info_cache_lock:
        # Evict any expired entries first if capacity reached
        if len(info_cache) >= INFO_CACHE_MAX_SIZE and url not in info_cache:
            expired = [k for k, v in info_cache.items() if v['expires_at'] <= now]
            for k in expired:
                del info_cache[k]
            # If still at capacity, evict oldest entry (first item in dict)
            if len(info_cache) >= INFO_CACHE_MAX_SIZE:
                oldest_key = next(iter(info_cache))
                del info_cache[oldest_key]
        info_cache[url] = {
            'data': data,
            'expires_at': now + INFO_CACHE_TTL_SECONDS,
        }

def cleanup_file(path, delay=3600):
    def _delete():
        time.sleep(delay)
        try:
            os.remove(path)
            temp_files.pop(path, None)
        except Exception:
            pass
    threading.Thread(target=_delete, daemon=True).start()

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

@app.route('/info', methods=['POST'])
def get_info():
    data = request.json
    if not data or not isinstance(data, dict):
        return jsonify({'error': 'URL required'}), 400
    url = data.get('url')
    if not url:
        return jsonify({'error': 'URL required'}), 400

    # Fast path: Return cached video info if available
    cached = get_cached_info(url)
    if cached is not None:
        return jsonify(cached)

    try:
        ydl_opts = {'quiet': True, 'no_warnings': True, 'skip_download': True}
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
    data = request.json
    url = data.get('url')
    start = float(data.get('start', 0))
    end = float(data.get('end', 60))
    format_type = data.get('format_type', 'video')
    quality = data.get('quality', '720p')

    if not url:
        return jsonify({'error': 'URL required'}), 400
    if end - start > 185:
        return jsonify({'error': 'Max 3 minutes allowed'}), 400

    quality_map = {'1080p': '1080', '720p': '720', '480p': '480', '360p': '360'}
    q = quality_map.get(quality, '720')

    try:
        tmpdir = tempfile.mkdtemp()
        ext = 'mp3' if format_type == 'audio' else 'mp4'
        out_path = os.path.join(tmpdir, f'clip.{ext}')

        if format_type == 'audio':
            audio_quality = '320' if quality == '320kbps' else '128'
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
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            # find the mp3
            for f in os.listdir(tmpdir):
                if f.endswith('.mp3'):
                    out_path = os.path.join(tmpdir, f)
                    break
        else:
            ydl_opts = {
                'format': f'bestvideo[height<={q}]+bestaudio/best[height<={q}]',
                'outtmpl': out_path,
                'merge_output_format': 'mp4',
                'download_ranges': yt_dlp.utils.download_range_func(None, [(start, end)]),
                'force_keyframes_at_cuts': True,
                'quiet': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        if not os.path.exists(out_path):
            return jsonify({'error': 'Download failed'}), 500

        temp_files[out_path] = True
        cleanup_file(out_path)

        return send_file(
            out_path,
            as_attachment=True,
            download_name=f'clip_{int(start)}_{int(end)}.{ext}',
            mimetype='audio/mpeg' if ext == 'mp3' else 'video/mp4'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
