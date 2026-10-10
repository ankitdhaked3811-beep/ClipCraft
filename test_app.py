import unittest
from unittest.mock import patch, MagicMock
from app import app, _get_video_info

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        _get_video_info.cache_clear()

    def test_health_endpoint(self):
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'status': 'ok'})

    def test_info_missing_url(self):
        response = self.app.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)

    @patch('app.yt_dlp.YoutubeDL')
    def test_info_success_and_caching(self, mock_ydl_cls):
        mock_ydl_instance = MagicMock()
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl_instance
        mock_ydl_instance.extract_info.return_value = {
            'title': 'Sample Title',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'http://example.com/thumb.jpg'
        }

        url = 'https://www.youtube.com/watch?v=mock123'

        # First call
        res1 = self.app.post('/info', json={'url': url})
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res1.json, {
            'title': 'Sample Title',
            'duration': 120,
            'channel': 'Test Channel',
            'thumbnail': 'http://example.com/thumb.jpg'
        })
        self.assertEqual(mock_ydl_instance.extract_info.call_count, 1)

        # Second call (cached hit)
        res2 = self.app.post('/info', json={'url': url})
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json, res1.json)
        # extract_info should not have been called a second time due to lru_cache
        self.assertEqual(mock_ydl_instance.extract_info.call_count, 1)

    def test_clip_validation(self):
        res = self.app.post('/clip', json={})
        self.assertEqual(res.status_code, 400)

        res_long = self.app.post('/clip', json={'url': 'http://test', 'start': 0, 'end': 300})
        self.assertEqual(res_long.status_code, 400)
        self.assertIn('Max 3 minutes allowed', res_long.json['error'])

if __name__ == '__main__':
    unittest.main()
