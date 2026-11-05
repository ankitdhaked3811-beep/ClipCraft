import os
import sys
import time
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app, video_info_cache


def benchmark():
    app.config['TESTING'] = True
    client = app.test_client()
    video_info_cache.clear()

    mock_ydl = MagicMock()
    mock_ydl.extract_info.return_value = {
        'title': 'Sample Video',
        'duration': 60,
        'uploader': 'Test User',
        'thumbnail': 'http://example.com/thumb.png',
    }

    url = 'https://www.youtube.com/watch?v=sample123'

    with patch('yt_dlp.YoutubeDL') as mock_ydl_cls:
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

        # Warm-up / Cache Miss
        t0 = time.perf_counter()
        res1 = client.post('/info', json={'url': url})
        miss_time = time.perf_counter() - t0
        assert res1.status_code == 200

        # Cache Hits
        iterations = 1000
        t0 = time.perf_counter()
        for _ in range(iterations):
            res = client.post('/info', json={'url': url})
            assert res.status_code == 200
        total_hit_time = time.perf_counter() - t0
        avg_hit_time = total_hit_time / iterations

    print('=== Benchmark Results ===')
    print(f'Cache Miss Latency: {miss_time * 1000:.3f} ms (without network delay)')
    print(f'Cache Hit Avg Latency: {avg_hit_time * 1000:.3f} ms ({iterations} runs)')
    print(f'Speedup (In-process): {miss_time / avg_hit_time:.1f}x faster')
    print('Note: Real yt-dlp network latency is typically 500ms - 2000ms.')
    print(f'Effective real-world speedup: ~{(1000 / (avg_hit_time * 1000)):.0f}x')


if __name__ == '__main__':
    benchmark()
