import unittest
from unittest.mock import patch
from app import app, _extract_video_info

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        _extract_video_info.cache_clear()

    def test_health(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'status': 'ok'})

    def test_info_missing_url(self):
        response = self.client.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)

    @patch('yt_dlp.YoutubeDL')
    def test_info_success_and_caching(self, mock_yt_dlp):
        mock_ydl_instance = mock_yt_dlp.return_value.__enter__.return_value
        mock_ydl_instance.extract_info.return_value = {
            'title': 'Test Title',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'http://example.com/thumb.jpg'
        }

        url = 'https://www.youtube.com/watch?v=test_id'

        # First request - cache miss
        response1 = self.client.post('/info', json={'url': url})
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response1.json['title'], 'Test Title')
        self.assertEqual(mock_ydl_instance.extract_info.call_count, 1)

        # Second request - cache hit
        response2 = self.client.post('/info', json={'url': url})
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.json['title'], 'Test Title')
        # mock call_count should remain 1 because info was retrieved from lru_cache
        self.assertEqual(mock_ydl_instance.extract_info.call_count, 1)

    def test_clip_validation(self):
        # Missing URL
        res = self.client.post('/clip', json={})
        self.assertEqual(res.status_code, 400)

        # Duration > 185s
        res = self.client.post('/clip', json={'url': 'http://example.com', 'start': 0, 'end': 200})
        self.assertEqual(res.status_code, 400)
        self.assertIn('Max 3 minutes allowed', res.json.get('error', ''))

if __name__ == '__main__':
    unittest.main()
