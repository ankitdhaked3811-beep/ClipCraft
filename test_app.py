import unittest
from unittest.mock import patch, MagicMock
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
    def test_info_success_and_caching(self, mock_ydl_class):
        mock_ydl_instance = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
        mock_ydl_instance.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'http://example.com/thumb.jpg'
        }

        url = 'https://www.youtube.com/watch?v=test'

        # First call
        response1 = self.client.post('/info', json={'url': url})
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response1.json, {
            'title': 'Test Video',
            'duration': 120,
            'channel': 'Test Channel',
            'thumbnail': 'http://example.com/thumb.jpg'
        })
        self.assertEqual(mock_ydl_instance.extract_info.call_count, 1)

        # Second call (should hit lru_cache)
        response2 = self.client.post('/info', json={'url': url})
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.json, response1.json)
        # Call count remains 1 due to caching
        self.assertEqual(mock_ydl_instance.extract_info.call_count, 1)

if __name__ == '__main__':
    unittest.main()
