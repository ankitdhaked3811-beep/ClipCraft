import unittest
from unittest.mock import patch
import time
import app

class AppTestCase(unittest.TestCase):
    def setUp(self):
        app.app.config['TESTING'] = True
        self.client = app.app.test_client()
        app.INFO_CACHE.clear()

    def test_health(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'status': 'ok'})

    def test_info_missing_url(self):
        response = self.client.post('/info', json={})
        self.assertEqual(response.status_code, 400)

    @patch('yt_dlp.YoutubeDL')
    def test_info_caching(self, mock_ydl_class):
        mock_ydl_instance = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl_instance.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'http://example.com/thumb.jpg',
        }

        url = 'https://www.youtube.com/watch?v=test12345'

        # First request - cache miss
        res1 = self.client.post('/info', json={'url': url})
        self.assertEqual(res1.status_code, 200)
        data1 = res1.get_json()
        self.assertEqual(data1['title'], 'Test Video')
        self.assertEqual(mock_ydl_instance.extract_info.call_count, 1)

        # Second request - cache hit (extract_info should NOT be called again)
        res2 = self.client.post('/info', json={'url': url})
        self.assertEqual(res2.status_code, 200)
        data2 = res2.get_json()
        self.assertEqual(data2, data1)
        self.assertEqual(mock_ydl_instance.extract_info.call_count, 1)

    @patch('yt_dlp.YoutubeDL')
    def test_info_cache_expiration(self, mock_ydl_class):
        mock_ydl_instance = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl_instance.extract_info.return_value = {
            'title': 'Test Video Expiry',
            'duration': 60,
            'uploader': 'Test Channel',
            'thumbnail': 'http://example.com/thumb.jpg',
        }

        url = 'https://www.youtube.com/watch?v=expiry'

        # Initial fetch
        self.client.post('/info', json={'url': url})
        self.assertEqual(mock_ydl_instance.extract_info.call_count, 1)

        # Simulate expiration
        app.INFO_CACHE[url] = (app.INFO_CACHE[url][0], time.time() - (app.CACHE_TTL_SECONDS + 10))

        # Subsequent fetch after expiration should call extract_info again
        self.client.post('/info', json={'url': url})
        self.assertEqual(mock_ydl_instance.extract_info.call_count, 2)

if __name__ == '__main__':
    unittest.main()
