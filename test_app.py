import unittest
from unittest.mock import patch
import app
import time

class TestApp(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()

    def test_health(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'status': 'ok'})

    def test_info_missing_url(self):
        response = self.client.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)

    @patch('app.yt_dlp.YoutubeDL')
    def test_info_success_and_caching(self, mock_ydl_cls):
        mock_ydl_instance = mock_ydl_cls.return_value.__enter__.return_value
        mock_ydl_instance.extract_info.return_value = {
            'title': 'Test Title',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'https://example.com/thumb.jpg'
        }

        # Clear cache before testing
        app.fetch_video_info.cache_clear()

        test_url = 'https://www.youtube.com/watch?v=test_caching'

        # First request - should call yt_dlp
        res1 = self.client.post('/info', json={'url': test_url})
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res1.json, {
            'title': 'Test Title',
            'duration': 120,
            'channel': 'Test Channel',
            'thumbnail': 'https://example.com/thumb.jpg'
        })
        self.assertEqual(mock_ydl_instance.extract_info.call_count, 1)

        # Second request - should hit LRU cache and not call yt_dlp again
        res2 = self.client.post('/info', json={'url': test_url})
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json, res1.json)
        self.assertEqual(mock_ydl_instance.extract_info.call_count, 1)

    def test_clip_validation(self):
        res1 = self.client.post('/clip', json={})
        self.assertEqual(res1.status_code, 400)

        res2 = self.client.post('/clip', json={'url': 'https://example.com/vid', 'start': 0, 'end': 200})
        self.assertEqual(res2.status_code, 400)
        self.assertIn('Max 3 minutes allowed', res2.json['error'])

if __name__ == '__main__':
    unittest.main()
