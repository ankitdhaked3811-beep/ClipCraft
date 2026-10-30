import unittest
from unittest.mock import patch, MagicMock
from app import app, fetch_video_info

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        # Clear LRU cache before each test
        fetch_video_info.cache_clear()

    def test_health_endpoint(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'status': 'ok'})

    def test_info_endpoint_missing_url(self):
        response = self.client.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)

    @patch('yt_dlp.YoutubeDL')
    def test_info_endpoint_and_lru_cache(self, mock_ydl_class):
        mock_ydl_instance = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
        mock_ydl_instance.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'https://example.com/thumb.jpg'
        }

        url = 'https://www.youtube.com/watch?v=test12345'

        # First request
        response1 = self.client.post('/info', json={'url': url})
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response1.json['title'], 'Test Video')
        self.assertEqual(mock_ydl_instance.extract_info.call_count, 1)

        # Check ydl_opts passed to YoutubeDL
        called_opts = mock_ydl_class.call_args[0][0]
        self.assertTrue(called_opts.get('noplaylist'))

        # Second request with same URL (should hit LRU cache and not call extract_info again)
        response2 = self.client.post('/info', json={'url': url})
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.json['title'], 'Test Video')
        self.assertEqual(mock_ydl_instance.extract_info.call_count, 1)

    def test_clip_endpoint_missing_url(self):
        response = self.client.post('/clip', json={})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {'error': 'URL required'})

    def test_clip_endpoint_exceed_duration(self):
        response = self.client.post('/clip', json={'url': 'https://example.com', 'start': 0, 'end': 200})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {'error': 'Max 3 minutes allowed'})

if __name__ == '__main__':
    unittest.main()
