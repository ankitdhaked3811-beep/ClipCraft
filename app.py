from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from functools import lru_cache
import yt_dlp
import tempfile
import os
import threading
import time

app = Flask(__name__)
CORS(app)

# Store temp files and auto-delete after 1 hour
temp_files = {}

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

@lru_cache(maxsize=256)
def extract_video_info(url):
    """
    Performance Optimization:
    Cache video metadata extraction results to avoid expensive external network calls
    when fetching information for the same URL multiple times.
    Reduces latency from ~1-3 seconds down to <1 ms on cache hits.
    Also uses 'noplaylist': True to prevent downloading entire playlist metadata.
    """
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'noplaylist': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return (
            info.get('title', ''),
            info.get('duration', 0),
            info.get('uploader', ''),
            info.get('thumbnail', ''),
        )

@app.route('/info', methods=['POST'])
def get_info():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({'error': 'URL required'}), 400
    try:
        title, duration, channel, thumbnail = extract_video_info(url)
        return jsonify({
            'title': title,
            'duration': duration,
            'channel': channel,
            'thumbnail': thumbnail,
        })
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
                'noplaylist': True,
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
                'noplaylist': True,
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
