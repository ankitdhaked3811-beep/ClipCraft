import unittest
from unittest.mock import patch, MagicMock
import time
import app

class AppTestCase(unittest.TestCase):
    def setUp(self):
        app.app.config['TESTING'] = True
        self.client = app.app.test_client()
        with app.info_cache_lock:
            app.info_cache.clear()

    def test_health_endpoint(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'status': 'ok'})

    def test_info_endpoint_missing_url(self):
        response = self.client.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

    def test_info_endpoint_invalid_body(self):
        response = self.client.post('/info', data='not json', content_type='text/plain')
        self.assertEqual(response.status_code, 415)

    @patch('app.yt_dlp.YoutubeDL')
    def test_info_endpoint_caching(self, mock_ydl_class):
        mock_ydl_instance = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
        mock_ydl_instance.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'https://example.com/thumb.jpg',
        }

        url = 'https://www.youtube.com/watch?v=mock123'

        # First call: cache miss, extracts from yt_dlp
        response1 = self.client.post('/info', json={'url': url})
        self.assertEqual(response1.status_code, 200)
        data1 = response1.get_json()
        self.assertEqual(data1['title'], 'Test Video')
        self.assertEqual(mock_ydl_instance.extract_info.call_count, 1)

        # Second call: cache hit, should NOT call yt_dlp again
        response2 = self.client.post('/info', json={'url': url})
        self.assertEqual(response2.status_code, 200)
        data2 = response2.get_json()
        self.assertEqual(data2, data1)
        self.assertEqual(mock_ydl_instance.extract_info.call_count, 1)

    @patch('app.yt_dlp.YoutubeDL')
    def test_info_endpoint_expiration(self, mock_ydl_class):
        mock_ydl_instance = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
        mock_ydl_instance.extract_info.return_value = {
            'title': 'Expiring Video',
            'duration': 60,
            'uploader': 'Exp Channel',
            'thumbnail': 'https://example.com/exp.jpg',
        }

        url = 'https://www.youtube.com/watch?v=expire123'
        self.client.post('/info', json={'url': url})
        self.assertEqual(mock_ydl_instance.extract_info.call_count, 1)

        # Force the cached item to be expired
        with app.info_cache_lock:
            app.info_cache[url]['expires_at'] = time.time() - 1

        # Third call: cache expired, extracts again
        self.client.post('/info', json={'url': url})
        self.assertEqual(mock_ydl_instance.extract_info.call_count, 2)

    def test_cache_lru_eviction(self):
        # Fill cache up to max size
        with app.info_cache_lock:
            app.INFO_CACHE_MAX_SIZE = 3
        try:
            app.set_cached_info('url1', {'title': '1'})
            app.set_cached_info('url2', {'title': '2'})
            app.set_cached_info('url3', {'title': '3'})
            # Access url1 to make url2 least recently used
            self.assertEqual(app.get_cached_info('url1'), {'title': '1'})
            # Insert url4, which should evict url2
            app.set_cached_info('url4', {'title': '4'})
            self.assertIsNotNone(app.get_cached_info('url1'))
            self.assertIsNone(app.get_cached_info('url2'))
            self.assertIsNotNone(app.get_cached_info('url3'))
            self.assertIsNotNone(app.get_cached_info('url4'))
        finally:
            with app.info_cache_lock:
                app.INFO_CACHE_MAX_SIZE = 256

if __name__ == '__main__':
    unittest.main()
