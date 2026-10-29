import unittest
from unittest.mock import patch
import time
from app import app, _fetch_video_info

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        # Clear lru_cache before each test
        _fetch_video_info.cache_clear()

    def test_health_endpoint(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'status': 'ok'})

    def test_info_endpoint_missing_url(self):
        response = self.client.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)

    @patch('app.yt_dlp.YoutubeDL')
    def test_info_endpoint_success_and_caching(self, mock_ydl_cls):
        mock_ydl = mock_ydl_cls.return_value.__enter__.return_value
        mock_ydl.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'https://example.com/thumb.jpg',
        }

        url = 'https://www.youtube.com/watch?v=test1234567'

        # First request - cache miss
        res1 = self.client.post('/info', json={'url': url})
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res1.json, {
            'title': 'Test Video',
            'duration': 120,
            'channel': 'Test Channel',
            'thumbnail': 'https://example.com/thumb.jpg',
        })
        self.assertEqual(mock_ydl.extract_info.call_count, 1)

        # Second request - cache hit (should not invoke YoutubeDL again)
        res2 = self.client.post('/info', json={'url': url})
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json, res1.json)
        # YoutubeDL extract_info should still have been called only once
        self.assertEqual(mock_ydl.extract_info.call_count, 1)

    def test_clip_endpoint_missing_url(self):
        response = self.client.post('/clip', json={})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {'error': 'URL required'})

    def test_clip_endpoint_duration_limit(self):
        response = self.client.post('/clip', json={
            'url': 'https://www.youtube.com/watch?v=test',
            'start': 0,
            'end': 200
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {'error': 'Max 3 minutes allowed'})

if __name__ == '__main__':
    unittest.main()
