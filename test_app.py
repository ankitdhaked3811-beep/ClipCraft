import unittest
import time
from unittest.mock import patch
from app import app, _fetch_video_info

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        _fetch_video_info.cache_clear()

    def test_health(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'status': 'ok'})

    def test_info_missing_url(self):
        response = self.client.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)

    @patch('yt_dlp.YoutubeDL')
    def test_info_caching_and_process_false(self, mock_ydl_cls):
        mock_ydl = mock_ydl_cls.return_value.__enter__.return_value
        mock_ydl.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'https://example.com/thumb.jpg',
        }

        url = 'https://www.youtube.com/watch?v=test12345'

        # First request
        res1 = self.client.post('/info', json={'url': url})
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res1.json['title'], 'Test Video')
        self.assertEqual(res1.json['duration'], 120)

        # Verify YoutubeDL extract_info was called with download=False, process=False
        mock_ydl.extract_info.assert_called_once_with(url, download=False, process=False)

        # Second request (cached)
        res2 = self.client.post('/info', json={'url': url})
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json['title'], 'Test Video')

        # extract_info should STILL have been called only once because second call hit LRU cache
        mock_ydl.extract_info.assert_called_once()
        self.assertEqual(_fetch_video_info.cache_info().hits, 1)

    def test_clip_missing_url(self):
        response = self.client.post('/clip', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)

    def test_clip_exceeds_max_duration(self):
        response = self.client.post('/clip', json={'url': 'http://example.com', 'start': 0, 'end': 300})
        self.assertEqual(response.status_code, 400)
        self.assertIn('Max 3 minutes allowed', response.json['error'])

if __name__ == '__main__':
    unittest.main()
