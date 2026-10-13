import unittest
from unittest.mock import patch, MagicMock
import tempfile
import os
import time
from app import app, info_cache, info_cache_lock, set_cached_info, get_cached_info, cleanup_file

class AppTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        with info_cache_lock:
            info_cache.clear()

    def test_health(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'status': 'ok'})

    def test_info_missing_url(self):
        response = self.client.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)

    @patch('yt_dlp.YoutubeDL')
    def test_info_uncached_and_caching(self, mock_ydl_cls):
        mock_ydl = MagicMock()
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = {
            'title': 'Sample Video',
            'duration': 120,
            'uploader': 'Sample Uploader',
            'thumbnail': 'https://example.com/thumb.jpg'
        }

        url = 'https://example.com/watch?v=123'

        # First request (uncached)
        response1 = self.client.post('/info', json={'url': url})
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response1.json, {
            'title': 'Sample Video',
            'duration': 120,
            'channel': 'Sample Uploader',
            'thumbnail': 'https://example.com/thumb.jpg'
        })
        # Verify process=False option passed to extract_info for speed
        mock_ydl.extract_info.assert_called_with(url, download=False, process=False)

        # Reset mock to ensure second call hits cache and doesn't invoke YoutubeDL
        mock_ydl_cls.reset_mock()

        # Second request (cached)
        response2 = self.client.post('/info', json={'url': url})
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.json, response1.json)
        mock_ydl_cls.assert_not_called()

    def test_clip_missing_url(self):
        response = self.client.post('/clip', json={})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {'error': 'URL required'})

    def test_clip_duration_limit(self):
        response = self.client.post('/clip', json={
            'url': 'https://example.com/watch?v=123',
            'start': 0,
            'end': 200
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {'error': 'Max 3 minutes allowed'})

    def test_cleanup_file(self):
        tmpdir = tempfile.mkdtemp()
        file_path = os.path.join(tmpdir, 'clip.mp4')
        with open(file_path, 'w') as f:
            f.write('dummy')

        cleanup_file(file_path, delay=0.05)
        time.sleep(0.2)

        self.assertFalse(os.path.exists(file_path))
        self.assertFalse(os.path.exists(tmpdir))

if __name__ == '__main__':
    unittest.main()
