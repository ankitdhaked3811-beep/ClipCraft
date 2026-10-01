import unittest
from unittest.mock import patch, MagicMock
from app import app, fetch_video_info

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        fetch_video_info.cache_clear()

    def test_health_endpoint(self):
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'status': 'ok'})

    def test_info_endpoint_missing_url(self):
        response = self.app.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(), {'error': 'URL required'})

    @patch('yt_dlp.YoutubeDL')
    def test_info_endpoint_and_caching(self, mock_yt_dlp):
        mock_instance = MagicMock()
        mock_instance.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'https://example.com/thumb.jpg',
        }
        mock_yt_dlp.return_value.__enter__.return_value = mock_instance

        url = 'https://www.youtube.com/watch?v=example'

        # First request
        response1 = self.app.post('/info', json={'url': url})
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response1.get_json(), {
            'title': 'Test Video',
            'duration': 120,
            'channel': 'Test Channel',
            'thumbnail': 'https://example.com/thumb.jpg'
        })
        self.assertEqual(mock_instance.extract_info.call_count, 1)

        # Second request (cached)
        response2 = self.app.post('/info', json={'url': url})
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.get_json(), response1.get_json())
        # extract_info should NOT have been called a second time due to lru_cache
        self.assertEqual(mock_instance.extract_info.call_count, 1)

if __name__ == '__main__':
    unittest.main()
