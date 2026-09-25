import unittest
from unittest.mock import patch
import app

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()
        app._extract_video_info.cache_clear()

    def test_health_endpoint(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'status': 'ok'})

    def test_info_missing_url(self):
        response = self.client.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)

    @patch('app.yt_dlp.YoutubeDL')
    def test_info_extraction_and_caching(self, mock_ytdl_cls):
        mock_ytdl = mock_ytdl_cls.return_value.__enter__.return_value
        mock_ytdl.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'http://example.com/thumb.jpg'
        }

        url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'

        # First request should call extract_info
        resp1 = self.client.post('/info', json={'url': url})
        self.assertEqual(resp1.status_code, 200)
        self.assertEqual(resp1.json['title'], 'Test Video')
        self.assertEqual(resp1.json['duration'], 120)
        self.assertEqual(resp1.json['channel'], 'Test Channel')
        self.assertEqual(resp1.json['thumbnail'], 'http://example.com/thumb.jpg')
        self.assertEqual(mock_ytdl.extract_info.call_count, 1)

        # Second request for the same URL should hit the LRU cache
        resp2 = self.client.post('/info', json={'url': url})
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.json, resp1.json)
        self.assertEqual(mock_ytdl.extract_info.call_count, 1)

        cache_info = app._extract_video_info.cache_info()
        self.assertEqual(cache_info.hits, 1)
        self.assertEqual(cache_info.misses, 1)

    def test_clip_duration_limit(self):
        response = self.client.post('/clip', json={
            'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'start': 0,
            'end': 200
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('Max 3 minutes allowed', response.json['error'])

    def test_clip_missing_url(self):
        response = self.client.post('/clip', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('URL required', response.json['error'])

if __name__ == '__main__':
    unittest.main()
