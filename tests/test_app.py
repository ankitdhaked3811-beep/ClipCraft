import unittest
from unittest.mock import patch, MagicMock
import time
import app

class TestApp(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()
        app.info_cache.clear()

    def tearDown(self):
        app.info_cache.clear()

    def test_health_endpoint(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'status': 'ok'})

    def test_info_endpoint_requires_url(self):
        response = self.client.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

    @patch('yt_dlp.YoutubeDL')
    def test_info_endpoint_caches_result(self, mock_ydl_cls):
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {
            'title': 'Test Title',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'https://example.com/thumb.jpg',
        }
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

        test_url = 'https://www.youtube.com/watch?v=mock123'

        # First request - cache miss
        resp1 = self.client.post('/info', json={'url': test_url})
        self.assertEqual(resp1.status_code, 200)
        data1 = resp1.get_json()
        self.assertEqual(data1['title'], 'Test Title')
        self.assertEqual(data1['duration'], 120)
        self.assertEqual(data1['channel'], 'Test Channel')
        self.assertEqual(data1['thumbnail'], 'https://example.com/thumb.jpg')
        self.assertEqual(mock_ydl.extract_info.call_count, 1)

        # Verify noplaylist is passed in options for faster extraction
        call_args, call_kwargs = mock_ydl_cls.call_args
        ydl_opts = call_args[0] if call_args else call_kwargs.get('params', {})
        self.assertTrue(ydl_opts.get('noplaylist'))

        # Second request - cache hit (extract_info should NOT be called again)
        resp2 = self.client.post('/info', json={'url': test_url})
        self.assertEqual(resp2.status_code, 200)
        data2 = resp2.get_json()
        self.assertEqual(data2, data1)
        self.assertEqual(mock_ydl.extract_info.call_count, 1)

    def test_cache_lru_and_ttl_behavior(self):
        cache = app.VideoMetadataCache(maxsize=2, ttl_seconds=1)
        cache.set('url1', {'data': 1})
        cache.set('url2', {'data': 2})

        self.assertEqual(cache.get('url1'), {'data': 1})
        self.assertEqual(cache.get('url2'), {'data': 2})

        # Insert 3rd item, url1 should be evicted if we access url2 after url1
        cache.set('url3', {'data': 3})
        # maxsize is 2, since url1 was accessed before url2, url1 was least recently used
        self.assertIsNone(cache.get('url1'))
        self.assertEqual(cache.get('url2'), {'data': 2})
        self.assertEqual(cache.get('url3'), {'data': 3})

        # Test TTL expiration
        time.sleep(1.05)
        self.assertIsNone(cache.get('url2'))
        self.assertIsNone(cache.get('url3'))

    def test_clip_endpoint_validation(self):
        # Missing url
        resp = self.client.post('/clip', json={})
        self.assertEqual(resp.status_code, 400)
        self.assertIn('URL required', resp.get_json()['error'])

        # Duration exceeding 185 seconds
        resp = self.client.post('/clip', json={'url': 'https://example.com', 'start': 0, 'end': 200})
        self.assertEqual(resp.status_code, 400)
        self.assertIn('Max 3 minutes allowed', resp.get_json()['error'])

if __name__ == '__main__':
    unittest.main()
