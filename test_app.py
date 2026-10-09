import unittest
from unittest.mock import patch, MagicMock
import app

class AppTestCase(unittest.TestCase):

    def setUp(self):
        self.client = app.app.test_client()
        app._extract_video_info.cache_clear()

    def test_health(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'status': 'ok'})

    def test_info_missing_url(self):
        response = self.client.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)

    @patch('yt_dlp.YoutubeDL')
    def test_info_success_and_caching(self, mock_ydl_cls):
        mock_ydl_instance = MagicMock()
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl_instance
        mock_ydl_instance.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'http://example.com/thumb.jpg'
        }

        url = 'https://www.youtube.com/watch?v=test12345'

        # First request
        res1 = self.client.post('/info', json={'url': url})
        self.assertEqual(res1.status_code, 200)
        expected_data = {
            'title': 'Test Video',
            'duration': 120,
            'channel': 'Test Channel',
            'thumbnail': 'http://example.com/thumb.jpg'
        }
        self.assertEqual(res1.json, expected_data)
        self.assertEqual(mock_ydl_instance.extract_info.call_count, 1)

        # Second request (should hit LRU cache, so YoutubeDL.extract_info is NOT called again)
        res2 = self.client.post('/info', json={'url': url})
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json, expected_data)
        self.assertEqual(mock_ydl_instance.extract_info.call_count, 1)

    def test_clip_missing_url(self):
        response = self.client.post('/clip', json={})
        self.assertEqual(response.status_code, 400)

    def test_clip_exceeds_max_duration(self):
        response = self.client.post('/clip', json={'url': 'http://example.com', 'start': 0, 'end': 200})
        self.assertEqual(response.status_code, 400)
        self.assertIn('Max 3 minutes allowed', response.json['error'])

if __name__ == '__main__':
    unittest.main()
