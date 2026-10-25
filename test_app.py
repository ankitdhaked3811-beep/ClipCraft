import unittest
from unittest.mock import patch, MagicMock
import app

class TestApp(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()
        # Clear cache before each test
        app._extract_info.cache_clear()

    def test_health(self):
        res = self.client.get('/health')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json, {'status': 'ok'})

    def test_info_missing_url(self):
        res = self.client.post('/info', json={})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json, {'error': 'URL required'})

    @patch('yt_dlp.YoutubeDL')
    def test_info_caching(self, mock_ydl_class):
        mock_ydl_instance = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
        mock_ydl_instance.extract_info.return_value = {
            'title': 'Test Title',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'http://example.com/thumb.jpg'
        }

        url = 'https://www.youtube.com/watch?v=test_id'

        # First request - cache miss (calls extract_info)
        res1 = self.client.post('/info', json={'url': url})
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res1.json, {
            'title': 'Test Title',
            'duration': 120,
            'channel': 'Test Channel',
            'thumbnail': 'http://example.com/thumb.jpg'
        })
        self.assertEqual(mock_ydl_instance.extract_info.call_count, 1)

        # Second request - cache hit (should NOT call extract_info again)
        res2 = self.client.post('/info', json={'url': url})
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json, {
            'title': 'Test Title',
            'duration': 120,
            'channel': 'Test Channel',
            'thumbnail': 'http://example.com/thumb.jpg'
        })
        # Call count remains 1 due to LRU cache!
        self.assertEqual(mock_ydl_instance.extract_info.call_count, 1)

    @patch('yt_dlp.YoutubeDL')
    def test_info_exception_handling(self, mock_ydl_class):
        mock_ydl_instance = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
        mock_ydl_instance.extract_info.side_effect = Exception('Extractor error')

        res = self.client.post('/info', json={'url': 'https://www.youtube.com/watch?v=invalid'})
        self.assertEqual(res.status_code, 500)
        self.assertIn('error', res.json)

    def test_clip_missing_url(self):
        res = self.client.post('/clip', json={})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json, {'error': 'URL required'})

    def test_clip_exceeds_max_duration(self):
        res = self.client.post('/clip', json={'url': 'http://example.com', 'start': 0, 'end': 200})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json, {'error': 'Max 3 minutes allowed'})

if __name__ == '__main__':
    unittest.main()
