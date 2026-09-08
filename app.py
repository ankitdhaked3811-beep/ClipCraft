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

# Thread-safe in-memory cache for video metadata to avoid redundant network extractions.
# Performance impact: Serves cached /info queries in <1ms instead of 1-3 seconds.
INFO_CACHE = {}
CACHE_LOCK = threading.Lock()
MAX_CACHE_SIZE = 256
CACHE_TTL = 3600  # Cache TTL in seconds (1 hour)

def get_cached_info(url):
    now = time.time()
    with CACHE_LOCK:
        if url in INFO_CACHE:
            cached_time, res = INFO_CACHE[url]
            if now - cached_time < CACHE_TTL:
                return res
            else:
                del INFO_CACHE[url]
    return None

def set_cached_info(url, res):
    now = time.time()
    with CACHE_LOCK:
        if len(INFO_CACHE) >= MAX_CACHE_SIZE:
            oldest_key = next(iter(INFO_CACHE))
            del INFO_CACHE[oldest_key]
        INFO_CACHE[url] = (now, res)

def cleanup_file(path, delay=3600):
    def _delete():
        time.sleep(delay)
        try:
            os.remove(path)
            temp_files.pop(path, None)
        except:
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

    # ⚡ Fast path: Return cached video info if available (<1ms vs 1-3s yt_dlp network request)
    cached = get_cached_info(url)
    if cached:
        return jsonify(cached)

    try:
        # ⚡ Optimization: 'noplaylist': True prevents yt_dlp from downloading/processing entire
        # playlists when playlist URLs are provided, avoiding long processing delays.
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'noplaylist': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        res = {
            'title': info.get('title', ''),
            'duration': info.get('duration', 0),
            'channel': info.get('uploader', ''),
            'thumbnail': info.get('thumbnail', ''),
        }

        # Cache result for subsequent requests
        set_cached_info(url, res)
        return jsonify(res)
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
                'noplaylist': True,
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
                'noplaylist': True,
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
