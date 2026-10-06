import unittest
from unittest.mock import patch
from app import app, fetch_video_info

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        # Clear cache before tests
        fetch_video_info.cache_clear()

    def test_health(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'status': 'ok'})

    def test_info_missing_url(self):
        response = self.client.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)

    def test_info_caching(self):
        test_url = 'https://example.com/test_video'
        mock_info = {
            'title': 'Test Video',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'https://example.com/thumb.jpg',
        }
        with patch('yt_dlp.YoutubeDL') as MockYDL:
            instance = MockYDL.return_value.__enter__.return_value
            instance.extract_info.return_value = mock_info

            # First call - should call YoutubeDL
            res1 = self.client.post('/info', json={'url': test_url})
            self.assertEqual(res1.status_code, 200)
            self.assertEqual(res1.json['title'], 'Test Video')
            self.assertEqual(instance.extract_info.call_count, 1)

            # Second call - should hit cache and NOT call YoutubeDL again
            res2 = self.client.post('/info', json={'url': test_url})
            self.assertEqual(res2.status_code, 200)
            self.assertEqual(res2.json['title'], 'Test Video')
            self.assertEqual(instance.extract_info.call_count, 1)

    def test_clip_missing_url(self):
        response = self.client.post('/clip', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)

    def test_clip_max_duration_exceeded(self):
        response = self.client.post('/clip', json={'url': 'https://example.com/vid', 'start': 0, 'end': 300})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {'error': 'Max 3 minutes allowed'})

if __name__ == '__main__':
    unittest.main()
