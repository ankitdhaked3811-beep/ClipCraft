import unittest
from unittest.mock import patch
import json
import app

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()
        app.fetch_video_info.cache_clear()

    def test_health(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'status': 'ok'})

    def test_info_missing_url(self):
        response = self.client.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

    @patch('yt_dlp.YoutubeDL')
    def test_info_success_and_caching(self, mock_ydl):
        mock_instance = mock_ydl.return_value.__enter__.return_value
        mock_instance.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'https://example.com/thumb.jpg',
        }

        url = 'https://www.youtube.com/watch?v=test12345'

        # First request - should invoke extract_info
        res1 = self.client.post('/info', json={'url': url})
        self.assertEqual(res1.status_code, 200)
        data1 = res1.get_json()
        self.assertEqual(data1['title'], 'Test Video')
        self.assertEqual(data1['duration'], 120)
        self.assertEqual(mock_instance.extract_info.call_count, 1)

        # Second request with same URL - should be served from LRU cache without extra extract_info call
        res2 = self.client.post('/info', json={'url': url})
        self.assertEqual(res2.status_code, 200)
        data2 = res2.get_json()
        self.assertEqual(data2['title'], 'Test Video')
        self.assertEqual(mock_instance.extract_info.call_count, 1)

    def test_clip_missing_url(self):
        response = self.client.post('/clip', json={})
        self.assertEqual(response.status_code, 400)

    def test_clip_exceeds_max_duration(self):
        response = self.client.post('/clip', json={'url': 'https://example.com', 'start': 0, 'end': 200})
        self.assertEqual(response.status_code, 400)
        self.assertIn('Max 3 minutes allowed', response.get_json().get('error', ''))

if __name__ == '__main__':
    unittest.main()
