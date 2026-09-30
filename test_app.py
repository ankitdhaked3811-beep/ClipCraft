import unittest
from unittest.mock import patch
import json
import app

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()
        app.extract_video_info.cache_clear()

    def test_health(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'status': 'ok'})

    def test_get_info_no_url(self):
        response = self.client.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

    @patch('app.yt_dlp.YoutubeDL')
    def test_get_info_caching_and_success(self, mock_yt_dlp):
        mock_ydl_instance = mock_yt_dlp.return_value.__enter__.return_value
        mock_ydl_instance.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'http://example.com/thumb.jpg'
        }

        url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'

        # First call - should hit extract_info
        response1 = self.client.post('/info', json={'url': url})
        self.assertEqual(response1.status_code, 200)
        data1 = response1.get_json()
        self.assertEqual(data1['title'], 'Test Video')
        self.assertEqual(data1['duration'], 120)
        self.assertEqual(data1['channel'], 'Test Channel')
        self.assertEqual(mock_ydl_instance.extract_info.call_count, 1)

        # Second call - should hit LRU cache and NOT call yt_dlp again
        response2 = self.client.post('/info', json={'url': url})
        self.assertEqual(response2.status_code, 200)
        data2 = response2.get_json()
        self.assertEqual(data2, data1)
        # Call count remains 1 due to cache
        self.assertEqual(mock_ydl_instance.extract_info.call_count, 1)

        cache_info = app.extract_video_info.cache_info()
        self.assertEqual(cache_info.hits, 1)
        self.assertEqual(cache_info.misses, 1)

    def test_clip_duration_limit(self):
        response = self.client.post('/clip', json={
            'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'start': 0,
            'end': 200
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('Max 3 minutes allowed', response.get_json()['error'])

if __name__ == '__main__':
    unittest.main()
