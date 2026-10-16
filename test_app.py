import unittest
from unittest.mock import patch, MagicMock
from app import app, fetch_video_info

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        fetch_video_info.cache_clear()

    def test_health_endpoint(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'status': 'ok'})

    @patch('yt_dlp.YoutubeDL')
    def test_info_endpoint_and_cache(self, mock_ydl_cls):
        mock_ydl_instance = MagicMock()
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl_instance
        mock_ydl_instance.extract_info.return_value = {
            'title': 'Test Title',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'http://example.com/thumb.jpg',
        }

        url = 'https://www.youtube.com/watch?v=mock123'

        # First request (cache miss)
        response1 = self.client.post('/info', json={'url': url})
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response1.get_json(), {
            'title': 'Test Title',
            'duration': 120,
            'channel': 'Test Channel',
            'thumbnail': 'http://example.com/thumb.jpg',
        })
        self.assertEqual(mock_ydl_instance.extract_info.call_count, 1)

        # Second request (cache hit)
        response2 = self.client.post('/info', json={'url': url})
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.get_json(), {
            'title': 'Test Title',
            'duration': 120,
            'channel': 'Test Channel',
            'thumbnail': 'http://example.com/thumb.jpg',
        })
        # Should still be 1 call count due to lru_cache
        self.assertEqual(mock_ydl_instance.extract_info.call_count, 1)

    def test_info_missing_url(self):
        response = self.client.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('URL required', response.get_json().get('error', ''))

    def test_clip_missing_url(self):
        response = self.client.post('/clip', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('URL required', response.get_json().get('error', ''))

    def test_clip_exceeds_max_duration(self):
        response = self.client.post('/clip', json={
            'url': 'https://www.youtube.com/watch?v=mock123',
            'start': 0,
            'end': 200
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('Max 3 minutes allowed', response.get_json().get('error', ''))

if __name__ == '__main__':
    unittest.main()
