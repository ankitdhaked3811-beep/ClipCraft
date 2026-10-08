import unittest
from unittest.mock import patch
import json
from app import app, _fetch_video_info

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        _fetch_video_info.cache_clear()

    def test_health_endpoint(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'status': 'ok'})

    def test_info_endpoint_missing_url(self):
        response = self.client.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

    @patch('yt_dlp.YoutubeDL')
    def test_info_endpoint_success_and_caching(self, mock_yt_dlp):
        mock_instance = mock_yt_dlp.return_value.__enter__.return_value
        mock_instance.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'https://example.com/thumb.jpg',
        }

        test_url = 'https://www.youtube.com/watch?v=test12345'

        # First request should trigger YoutubeDL.extract_info
        response1 = self.client.post('/info', json={'url': test_url})
        self.assertEqual(response1.status_code, 200)
        data1 = response1.get_json()
        self.assertEqual(data1['title'], 'Test Video')
        self.assertEqual(data1['duration'], 120)
        self.assertEqual(data1['channel'], 'Test Channel')
        self.assertEqual(data1['thumbnail'], 'https://example.com/thumb.jpg')
        self.assertEqual(mock_instance.extract_info.call_count, 1)

        # Second request with same URL should hit LRU cache and NOT invoke YoutubeDL
        response2 = self.client.post('/info', json={'url': test_url})
        self.assertEqual(response2.status_code, 200)
        data2 = response2.get_json()
        self.assertEqual(data2, data1)
        self.assertEqual(mock_instance.extract_info.call_count, 1)

    @patch('yt_dlp.YoutubeDL')
    def test_info_endpoint_exception(self, mock_yt_dlp):
        mock_instance = mock_yt_dlp.return_value.__enter__.return_value
        mock_instance.extract_info.side_effect = Exception('Download error')

        response = self.client.post('/info', json={'url': 'https://www.youtube.com/watch?v=invalid'})
        self.assertEqual(response.status_code, 500)
        self.assertIn('error', response.get_json())

if __name__ == '__main__':
    unittest.main()
