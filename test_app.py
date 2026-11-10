import time
import unittest
from unittest.mock import patch

from app import TTLLRUCache, app, info_cache


class TestApp(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        info_cache.clear()

    def test_health_endpoint(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'status': 'ok'})

    def test_ttl_lru_cache_operations(self):
        cache = TTLLRUCache(capacity=2, ttl_seconds=1)
        cache.set('k1', 'v1')
        cache.set('k2', 'v2')

        # Cache hit
        self.assertEqual(cache.get('k1'), 'v1')

        # Capacity eviction (k2 should be evicted since k1 was accessed)
        cache.set('k3', 'v3')
        self.assertEqual(cache.get('k1'), 'v1')
        self.assertIsNone(cache.get('k2'))
        self.assertEqual(cache.get('k3'), 'v3')

        # TTL expiration
        time.sleep(1.05)
        self.assertIsNone(cache.get('k1'))
        self.assertIsNone(cache.get('k3'))

    def test_info_endpoint_validation(self):
        # Empty payload
        response = self.client.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

        # Missing url key
        response = self.client.post('/info', json={'other': 'val'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

    @patch('yt_dlp.YoutubeDL')
    def test_info_endpoint_caching(self, mock_ydl_cls):
        mock_ydl_instance = mock_ydl_cls.return_value.__enter__.return_value
        mock_ydl_instance.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 120,
            'uploader': 'Test Creator',
            'thumbnail': 'https://example.com/thumb.jpg',
        }

        url = 'https://www.youtube.com/watch?v=mock123'

        # First request - cache miss: calls yt_dlp
        resp1 = self.client.post('/info', json={'url': url})
        self.assertEqual(resp1.status_code, 200)
        data1 = resp1.get_json()
        self.assertEqual(data1['title'], 'Test Video')
        self.assertEqual(mock_ydl_instance.extract_info.call_count, 1)

        # Second request - cache hit: serves directly from memory without calling yt_dlp
        resp2 = self.client.post('/info', json={'url': url})
        self.assertEqual(resp2.status_code, 200)
        data2 = resp2.get_json()
        self.assertEqual(data2['title'], 'Test Video')
        self.assertEqual(mock_ydl_instance.extract_info.call_count, 1)

    def test_clip_endpoint_validation(self):
        # Missing url
        resp1 = self.client.post('/clip', json={'url': ''})
        self.assertEqual(resp1.status_code, 400)

        # Duration exceeding 3 minutes (185s limit)
        resp2 = self.client.post('/clip', json={'url': 'https://example.com', 'start': 0, 'end': 200})
        self.assertEqual(resp2.status_code, 400)
        self.assertIn('Max 3 minutes allowed', resp2.get_json()['error'])


if __name__ == '__main__':
    unittest.main()
