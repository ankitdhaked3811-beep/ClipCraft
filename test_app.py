import unittest
from unittest.mock import patch
import json
import time
from app import app, fetch_video_info

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        fetch_video_info.cache_clear()

    def test_health_endpoint(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'status': 'ok'})

    def test_info_endpoint_missing_url(self):
        response = self.client.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

    @patch('yt_dlp.YoutubeDL')
    def test_info_endpoint_and_lru_cache(self, mock_ydl_cls):
        mock_instance = mock_ydl_cls.return_value.__enter__.return_value
        mock_instance.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 100,
            'uploader': 'Test Channel',
            'thumbnail': 'https://example.com/thumb.jpg'
        }

        url = 'https://example.com/watch?v=test'

        # First request - cache miss
        t0 = time.time()
        response1 = self.client.post('/info', json={'url': url})
        t1 = time.time()
        time_miss = t1 - t0

        self.assertEqual(response1.status_code, 200)
        data1 = response1.get_json()
        self.assertEqual(data1['title'], 'Test Video')
        self.assertEqual(data1['duration'], 100)
        self.assertEqual(data1['channel'], 'Test Channel')
        self.assertEqual(data1['thumbnail'], 'https://example.com/thumb.jpg')
        self.assertEqual(mock_instance.extract_info.call_count, 1)

        # Second request - cache hit
        t2 = time.time()
        response2 = self.client.post('/info', json={'url': url})
        t3 = time.time()
        time_hit = t3 - t2

        self.assertEqual(response2.status_code, 200)
        data2 = response2.get_json()
        self.assertEqual(data2, data1)
        # Should NOT call extract_info again
        self.assertEqual(mock_instance.extract_info.call_count, 1)

        print(f"\n[CACHE TEST] Miss time: {time_miss*1000:.3f}ms | Hit time: {time_hit*1000:.3f}ms")

if __name__ == '__main__':
    unittest.main()
