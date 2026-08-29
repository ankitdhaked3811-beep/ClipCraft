import unittest
from unittest.mock import patch, MagicMock
from app import app

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_health(self):
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'status': 'ok'})

    def test_info_missing_url(self):
        response = self.app.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {'error': 'URL required'})

    @patch('yt_dlp.YoutubeDL')
    def test_info_success_and_caching(self, mock_ydl_cls):
        mock_ydl = MagicMock()
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'https://example.com/thumb.jpg'
        }

        url = 'https://example.com/watch?v=unique_test_video'

        # First call - cache miss
        response1 = self.app.post('/info', json={'url': url})
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response1.json, {
            'title': 'Test Video',
            'duration': 120,
            'channel': 'Test Channel',
            'thumbnail': 'https://example.com/thumb.jpg'
        })

        # Second call - cache hit
        response2 = self.app.post('/info', json={'url': url})
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.json, response1.json)

        # yt_dlp extract_info should only have been called once due to caching
        mock_ydl.extract_info.assert_called_once()

    def test_clip_missing_url(self):
        response = self.app.post('/clip', json={})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {'error': 'URL required'})

    def test_clip_exceeds_max_duration(self):
        response = self.app.post('/clip', json={'url': 'https://example.com/watch?v=123', 'start': 0, 'end': 200})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {'error': 'Max 3 minutes allowed'})

if __name__ == '__main__':
    unittest.main()
