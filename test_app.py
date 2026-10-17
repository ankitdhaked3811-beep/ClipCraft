import unittest
from unittest.mock import patch, MagicMock
from app import app, _extract_info_cached

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_health(self):
        res = self.client.get('/health')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json, {'status': 'ok'})

    def test_info_missing_url(self):
        res = self.client.post('/info', json={})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json, {'error': 'URL required'})

    @patch('yt_dlp.YoutubeDL')
    def test_info_success_and_caching(self, mock_yt_dlp):
        _extract_info_cached.cache_clear()
        mock_instance = MagicMock()
        mock_instance.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'http://example.com/thumb.jpg'
        }
        mock_yt_dlp.return_value.__enter__.return_value = mock_instance

        url = 'https://example.com/watch?v=unique123'

        # First request - cache miss
        res1 = self.client.post('/info', json={'url': url})
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res1.json, {
            'title': 'Test Video',
            'duration': 120,
            'channel': 'Test Channel',
            'thumbnail': 'http://example.com/thumb.jpg'
        })

        # Verify noplaylist is passed to YoutubeDL options
        mock_yt_dlp.assert_called_with({
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'noplaylist': True,
        })
        self.assertEqual(mock_instance.extract_info.call_count, 1)

        # Second request for same URL - cache hit
        res2 = self.client.post('/info', json={'url': url})
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json, res1.json)

        # extract_info should NOT have been called a second time
        self.assertEqual(mock_instance.extract_info.call_count, 1)

    def test_clip_missing_url(self):
        res = self.client.post('/clip', json={})
        self.assertEqual(res.status_code, 400)

    def test_clip_exceeds_max_duration(self):
        res = self.client.post('/clip', json={'url': 'http://example.com', 'start': 0, 'end': 200})
        self.assertEqual(res.status_code, 400)
        self.assertIn('Max 3 minutes allowed', res.json['error'])

if __name__ == '__main__':
    unittest.main()
