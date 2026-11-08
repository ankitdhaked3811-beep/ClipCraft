import unittest
from unittest.mock import patch, MagicMock
import time
import app

class AppTestCase(unittest.TestCase):
    def setUp(self):
        app.app.config['TESTING'] = True
        self.client = app.app.test_client()
        with app._info_cache_lock:
            app._info_cache.clear()

    def tearDown(self):
        with app._info_cache_lock:
            app._info_cache.clear()

    def test_health_endpoint(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'status': 'ok'})

    def test_info_endpoint_missing_url(self):
        response = self.client.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

    @patch('app.yt_dlp.YoutubeDL')
    def test_info_endpoint_caches_result(self, mock_ydl_cls):
        mock_instance = MagicMock()
        mock_instance.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'https://example.com/thumb.jpg',
        }
        mock_ydl_cls.return_value.__enter__.return_value = mock_instance

        # First request should extract info via yt_dlp
        res1 = self.client.post('/info', json={'url': 'https://youtube.com/watch?v=123'})
        self.assertEqual(res1.status_code, 200)
        data1 = res1.get_json()
        self.assertEqual(data1['title'], 'Test Video')
        self.assertEqual(data1['duration'], 120)
        self.assertEqual(data1['channel'], 'Test Channel')
        self.assertEqual(data1['thumbnail'], 'https://example.com/thumb.jpg')
        self.assertEqual(mock_instance.extract_info.call_count, 1)

        # Second request with the same URL should hit the cache without calling extract_info again
        res2 = self.client.post('/info', json={'url': 'https://youtube.com/watch?v=123'})
        self.assertEqual(res2.status_code, 200)
        data2 = res2.get_json()
        self.assertEqual(data2, data1)
        self.assertEqual(mock_instance.extract_info.call_count, 1)

    @patch('app.yt_dlp.YoutubeDL')
    def test_info_cache_expiry(self, mock_ydl_cls):
        mock_instance = MagicMock()
        mock_instance.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'https://example.com/thumb.jpg',
        }
        mock_ydl_cls.return_value.__enter__.return_value = mock_instance

        test_url = 'https://youtube.com/watch?v=expired'
        self.client.post('/info', json={'url': test_url})
        self.assertEqual(mock_instance.extract_info.call_count, 1)

        # Artificially age the cached entry past TTL
        with app._info_cache_lock:
            app._info_cache[test_url] = (time.time() - (app.INFO_CACHE_TTL + 10), app._info_cache[test_url][1])

        # Request again should re-fetch because of expiration
        res = self.client.post('/info', json={'url': test_url})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(mock_instance.extract_info.call_count, 2)

    def test_info_cache_max_size_eviction(self):
        for i in range(app.INFO_CACHE_MAX_SIZE):
            app.set_cached_info(f'url_{i}', {'title': f'Title {i}'})

        self.assertEqual(len(app._info_cache), app.INFO_CACHE_MAX_SIZE)
        self.assertIsNotNone(app.get_cached_info('url_0'))

        # Adding one more item should evict the oldest key (which is now url_1 after url_0 was accessed, or oldest in dict)
        app.set_cached_info('url_new', {'title': 'New'})
        self.assertEqual(len(app._info_cache), app.INFO_CACHE_MAX_SIZE)
        self.assertIsNotNone(app.get_cached_info('url_new'))

    @patch('app.yt_dlp.YoutubeDL')
    def test_info_exception_handling(self, mock_ydl_cls):
        mock_instance = MagicMock()
        mock_instance.extract_info.side_effect = Exception("Extraction failed")
        mock_ydl_cls.return_value.__enter__.return_value = mock_instance

        response = self.client.post('/info', json={'url': 'https://youtube.com/watch?v=err'})
        self.assertEqual(response.status_code, 500)
        self.assertIn('Extraction failed', response.get_json()['error'])

    def test_clip_validation(self):
        # Missing URL
        res = self.client.post('/clip', json={'start': 0, 'end': 30})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.get_json(), {'error': 'URL required'})

        # Duration > 185s
        res = self.client.post('/clip', json={'url': 'https://test', 'start': 0, 'end': 200})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.get_json(), {'error': 'Max 3 minutes allowed'})

if __name__ == '__main__':
    unittest.main()
