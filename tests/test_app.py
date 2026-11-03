import unittest
from unittest.mock import patch, MagicMock
import app

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()
        app._info_cache.clear()

    def test_health(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'status': 'ok'})

    def test_info_missing_url(self):
        response = self.client.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('URL required', response.get_json()['error'])

    @patch('yt_dlp.YoutubeDL')
    def test_info_success_and_caching(self, mock_ydl_cls):
        mock_instance = MagicMock()
        mock_ydl_cls.return_value.__enter__.return_value = mock_instance
        mock_instance.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'https://example.com/thumb.jpg',
        }

        # First call: cache miss, extracts from yt_dlp
        url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        response1 = self.client.post('/info', json={'url': url})
        self.assertEqual(response1.status_code, 200)
        data1 = response1.get_json()
        self.assertEqual(data1['title'], 'Test Video')
        self.assertEqual(data1['duration'], 120)
        self.assertEqual(data1['channel'], 'Test Channel')
        self.assertEqual(mock_instance.extract_info.call_count, 1)

        # Second call: cache hit, yt_dlp should NOT be called again
        response2 = self.client.post('/info', json={'url': url})
        self.assertEqual(response2.status_code, 200)
        data2 = response2.get_json()
        self.assertEqual(data2, data1)
        self.assertEqual(mock_instance.extract_info.call_count, 1)

    @patch('yt_dlp.YoutubeDL')
    def test_info_cache_eviction(self, mock_ydl_cls):
        mock_instance = MagicMock()
        mock_ydl_cls.return_value.__enter__.return_value = mock_instance
        mock_instance.extract_info.return_value = {'title': 'Video'}

        # Fill cache past max size limit
        with patch.object(app, 'INFO_CACHE_MAX_SIZE', 2):
            self.client.post('/info', json={'url': 'url1'})
            self.client.post('/info', json={'url': 'url2'})
            self.assertEqual(len(app._info_cache), 2)
            self.assertIn('url1', app._info_cache)

            # Insert 3rd URL, url1 should be evicted (FIFO)
            self.client.post('/info', json={'url': 'url3'})
            self.assertEqual(len(app._info_cache), 2)
            self.assertNotIn('url1', app._info_cache)
            self.assertIn('url3', app._info_cache)

    @patch('yt_dlp.YoutubeDL')
    def test_info_error_handling(self, mock_ydl_cls):
        mock_instance = MagicMock()
        mock_ydl_cls.return_value.__enter__.return_value = mock_instance
        mock_instance.extract_info.side_effect = RuntimeError('Extraction error')

        response = self.client.post('/info', json={'url': 'https://example.com/bad'})
        self.assertEqual(response.status_code, 500)
        self.assertIn('Extraction error', response.get_json()['error'])

    def test_clip_missing_url(self):
        response = self.client.post('/clip', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('URL required', response.get_json()['error'])

    def test_clip_duration_exceeded(self):
        response = self.client.post('/clip', json={
            'url': 'https://youtube.com/watch?v=abc',
            'start': 0,
            'end': 200
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('Max 3 minutes allowed', response.get_json()['error'])

if __name__ == '__main__':
    unittest.main()
