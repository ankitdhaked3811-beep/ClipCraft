import unittest
from unittest.mock import patch, MagicMock
from app import app, _fetch_video_info

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        # Clear cache before tests
        _fetch_video_info.cache_clear()

    def test_health_endpoint(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'status': 'ok'})

    def test_info_missing_url(self):
        response = self.client.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)

    @patch('yt_dlp.YoutubeDL')
    def test_info_success_and_caching(self, mock_yt_dlp):
        mock_instance = MagicMock()
        mock_yt_dlp.return_value.__enter__.return_value = mock_instance
        mock_instance.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'https://example.com/thumb.jpg',
        }

        url = 'https://example.com/watch?v=test1234'

        # First request should hit YoutubeDL
        res1 = self.client.post('/info', json={'url': url})
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res1.json['title'], 'Test Video')
        self.assertEqual(res1.json['duration'], 120)
        self.assertEqual(res1.json['channel'], 'Test Channel')
        self.assertEqual(res1.json['thumbnail'], 'https://example.com/thumb.jpg')

        self.assertEqual(mock_instance.extract_info.call_count, 1)

        # Second request with same URL should hit LRU cache and NOT call YoutubeDL again
        res2 = self.client.post('/info', json={'url': url})
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json, res1.json)

        # Call count should still be 1 because of caching!
        self.assertEqual(mock_instance.extract_info.call_count, 1)

    def test_clip_missing_url(self):
        response = self.client.post('/clip', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)

    def test_clip_exceeds_max_duration(self):
        response = self.client.post('/clip', json={'url': 'https://example.com/v', 'start': 0, 'end': 200})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {'error': 'Max 3 minutes allowed'})

if __name__ == '__main__':
    unittest.main()
