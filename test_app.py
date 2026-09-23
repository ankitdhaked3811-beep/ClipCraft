import unittest
from unittest.mock import patch
import app

class AppTestCase(unittest.TestCase):
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

    @patch('yt_dlp.YoutubeDL')
    def test_info_success(self, mock_ydl_cls):
        mock_ydl = mock_ydl_cls.return_value.__enter__.return_value
        mock_ydl.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'http://example.com/thumb.jpg'
        }

        response = self.client.post('/info', json={'url': 'https://youtube.com/watch?v=test12345'})
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data['title'], 'Test Video')
        self.assertEqual(data['duration'], 120)
        self.assertEqual(data['channel'], 'Test Channel')
        self.assertEqual(data['thumbnail'], 'http://example.com/thumb.jpg')

    @patch('yt_dlp.YoutubeDL')
    def test_get_yt_info_caching(self, mock_ydl_cls):
        mock_ydl = mock_ydl_cls.return_value.__enter__.return_value
        mock_ydl.extract_info.return_value = {
            'title': 'Cached Title',
            'duration': 60,
            'uploader': 'Cached Channel',
            'thumbnail': 'http://example.com/cached.jpg'
        }

        url = "https://www.youtube.com/watch?v=cached_test_video"

        # Clear cache before test
        app._get_yt_info.cache_clear()

        res1 = self.client.post('/info', json={'url': url})
        self.assertEqual(res1.status_code, 200)

        res2 = self.client.post('/info', json={'url': url})
        self.assertEqual(res2.status_code, 200)

        # Ensure extract_info was called only ONCE due to LRU cache
        self.assertEqual(mock_ydl.extract_info.call_count, 1)

    def test_clip_missing_url(self):
        response = self.client.post('/clip', json={})
        self.assertEqual(response.status_code, 400)

    def test_clip_too_long(self):
        response = self.client.post('/clip', json={'url': 'https://youtube.com/watch?v=test', 'start': 0, 'end': 200})
        self.assertEqual(response.status_code, 400)

if __name__ == '__main__':
    unittest.main()
