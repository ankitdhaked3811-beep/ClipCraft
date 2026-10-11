import unittest
from unittest.mock import patch
import yt_dlp
from app import app, _extract_video_info

class TestClipCraftBackend(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        _extract_video_info.cache_clear()

    def test_health_endpoint(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'status': 'ok'})

    def test_info_endpoint_missing_url(self):
        response = self.client.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)

    @patch.object(yt_dlp.YoutubeDL, 'extract_info')
    def test_info_endpoint_caching(self, mock_extract):
        mock_extract.return_value = {
            'title': 'Test Video Title',
            'duration': 180,
            'uploader': 'Test Channel',
            'thumbnail': 'https://example.com/thumb.jpg',
        }

        test_url = 'https://example.com/watch?v=cached_test'

        # First request
        resp1 = self.client.post('/info', json={'url': test_url})
        self.assertEqual(resp1.status_code, 200)
        self.assertEqual(resp1.json['title'], 'Test Video Title')
        self.assertEqual(mock_extract.call_count, 1)

        # Second request for same URL (should hit LRU cache)
        resp2 = self.client.post('/info', json={'url': test_url})
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.json['title'], 'Test Video Title')
        # mock_extract should NOT have been called again
        self.assertEqual(mock_extract.call_count, 1)

    def test_clip_endpoint_missing_url(self):
        response = self.client.post('/clip', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)

    def test_clip_endpoint_exceeds_max_duration(self):
        response = self.client.post('/clip', json={
            'url': 'https://example.com/watch?v=test',
            'start': 0,
            'end': 200  # > 185 seconds
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {'error': 'Max 3 minutes allowed'})

if __name__ == '__main__':
    unittest.main()
