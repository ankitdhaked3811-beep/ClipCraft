import unittest
from unittest.mock import patch, MagicMock
from app import app, info_cache

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        info_cache.clear()

    def test_health(self):
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'status': 'ok'})

    def test_info_missing_url(self):
        response = self.app.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

    @patch('yt_dlp.YoutubeDL')
    def test_info_caching(self, mock_ydl_cls):
        mock_ydl = MagicMock()
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'http://example.com/thumb.jpg'
        }

        # First request - cache miss
        resp1 = self.app.post('/info', json={'url': 'https://www.youtube.com/watch?v=test1234'})
        self.assertEqual(resp1.status_code, 200)
        data1 = resp1.get_json()
        self.assertEqual(data1['title'], 'Test Video')
        self.assertEqual(mock_ydl.extract_info.call_count, 1)

        # Second request - cache hit
        resp2 = self.app.post('/info', json={'url': 'https://www.youtube.com/watch?v=test1234'})
        self.assertEqual(resp2.status_code, 200)
        data2 = resp2.get_json()
        self.assertEqual(data2, data1)
        # Call count should still be 1 because of cache hit
        self.assertEqual(mock_ydl.extract_info.call_count, 1)

    @patch('yt_dlp.YoutubeDL')
    @patch('time.time')
    def test_info_cache_expiration(self, mock_time, mock_ydl_cls):
        mock_time.return_value = 1000.0
        mock_ydl = MagicMock()
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = {'title': 'Test Video', 'duration': 120, 'uploader': 'Test', 'thumbnail': ''}

        # Request at t = 1000
        self.app.post('/info', json={'url': 'http://example.com/video'})
        self.assertEqual(mock_ydl.extract_info.call_count, 1)

        # Request at t = 2000 (cache hit, ttl is 3600)
        mock_time.return_value = 2000.0
        self.app.post('/info', json={'url': 'http://example.com/video'})
        self.assertEqual(mock_ydl.extract_info.call_count, 1)

        # Request at t = 5000 (expired, cache miss)
        mock_time.return_value = 5000.0
        self.app.post('/info', json={'url': 'http://example.com/video'})
        self.assertEqual(mock_ydl.extract_info.call_count, 2)

    def test_clip_missing_url(self):
        response = self.app.post('/clip', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

    def test_clip_exceeds_max_duration(self):
        response = self.app.post('/clip', json={'url': 'http://example.com', 'start': 0, 'end': 200})
        self.assertEqual(response.status_code, 400)
        self.assertIn('Max 3 minutes allowed', response.get_json()['error'])

if __name__ == '__main__':
    unittest.main()
