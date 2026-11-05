import unittest
from unittest.mock import patch, MagicMock
import os
import tempfile
import time
from app import app, video_info_cache, TTLCache, cleanup_file


class TestClipCraftBackend(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        video_info_cache.clear()

    def tearDown(self):
        video_info_cache.clear()

    def test_health(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'status': 'ok'})

    def test_info_missing_url(self):
        response = self.client.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

    @patch('yt_dlp.YoutubeDL')
    def test_info_cache_hit_and_miss(self, mock_ydl_cls):
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'http://example.com/thumb.jpg',
        }
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

        url = 'https://www.youtube.com/watch?v=123456'

        # First call (cache miss) - invokes yt_dlp
        response1 = self.client.post('/info', json={'url': url})
        self.assertEqual(response1.status_code, 200)
        data1 = response1.get_json()
        self.assertEqual(data1['title'], 'Test Video')
        self.assertEqual(data1['duration'], 120)
        self.assertEqual(data1['channel'], 'Test Channel')
        self.assertEqual(data1['thumbnail'], 'http://example.com/thumb.jpg')
        self.assertEqual(mock_ydl.extract_info.call_count, 1)

        # Second call (cache hit) - does NOT invoke yt_dlp
        response2 = self.client.post('/info', json={'url': url})
        self.assertEqual(response2.status_code, 200)
        data2 = response2.get_json()
        self.assertEqual(data2, data1)
        self.assertEqual(mock_ydl.extract_info.call_count, 1)

    @patch('yt_dlp.YoutubeDL')
    def test_info_error_handling(self, mock_ydl_cls):
        mock_ydl = MagicMock()
        mock_ydl.extract_info.side_effect = RuntimeError('yt-dlp extraction error')
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

        response = self.client.post('/info', json={'url': 'http://example.com/fail'})
        self.assertEqual(response.status_code, 500)
        self.assertIn('error', response.get_json())

    def test_ttl_cache_eviction_and_expiry(self):
        cache = TTLCache(maxsize=2, ttl=0.1)
        cache.set('key1', 'val1')
        cache.set('key2', 'val2')

        # Test get and order update
        self.assertEqual(cache.get('key1'), 'val1')

        # Exceed capacity
        cache.set('key3', 'val3')
        self.assertEqual(cache.get('key1'), 'val1')
        self.assertIsNone(cache.get('key2'))  # key2 evicted as oldest
        self.assertEqual(cache.get('key3'), 'val3')

        # Expiry
        time.sleep(0.15)
        self.assertIsNone(cache.get('key1'))
        self.assertIsNone(cache.get('key3'))

    def test_clip_validation(self):
        # Missing URL
        response = self.client.post('/clip', json={})
        self.assertEqual(response.status_code, 400)

        # Duration exceeding max allowed (185s)
        response = self.client.post('/clip', json={'url': 'http://example.com', 'start': 0, 'end': 200})
        self.assertEqual(response.status_code, 400)
        self.assertIn('Max 3 minutes allowed', response.get_json().get('error', ''))

    def test_cleanup_file_removes_temp_dir(self):
        tmpdir = tempfile.mkdtemp()
        file_path = os.path.join(tmpdir, 'clip.mp4')
        with open(file_path, 'w') as f:
            f.write('dummy')

        self.assertTrue(os.path.exists(file_path))
        self.assertTrue(os.path.exists(tmpdir))

        cleanup_file(file_path, delay=0.05)
        time.sleep(0.15)

        self.assertFalse(os.path.exists(file_path))
        self.assertFalse(os.path.exists(tmpdir))


if __name__ == '__main__':
    unittest.main()
