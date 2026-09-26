import unittest
from unittest.mock import patch, MagicMock
from app import app, fetch_video_info

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        fetch_video_info.cache_clear()

    def test_health_endpoint(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'status': 'ok'})

    def test_info_missing_url(self):
        response = self.client.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

    @patch('yt_dlp.YoutubeDL')
    def test_info_success_and_caching(self, mock_ydl_cls):
        mock_ydl = MagicMock()
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'http://example.com/thumb.jpg'
        }

        url = 'https://www.youtube.com/watch?v=test12345'

        # First request
        resp1 = self.client.post('/info', json={'url': url})
        self.assertEqual(resp1.status_code, 200)
        data1 = resp1.get_json()
        self.assertEqual(data1['title'], 'Test Video')
        self.assertEqual(data1['duration'], 120)
        self.assertEqual(data1['channel'], 'Test Channel')
        self.assertEqual(data1['thumbnail'], 'http://example.com/thumb.jpg')

        # Verify extract_info was called once
        self.assertEqual(mock_ydl.extract_info.call_count, 1)

        # Second request with the same URL should hit the cache
        resp2 = self.client.post('/info', json={'url': url})
        self.assertEqual(resp2.status_code, 200)
        data2 = resp2.get_json()
        self.assertEqual(data2, data1)

        # Verify extract_info was STILL called only once (cached hit)
        self.assertEqual(mock_ydl.extract_info.call_count, 1)

    def test_clip_missing_url(self):
        response = self.client.post('/clip', json={})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(), {'error': 'URL required'})

    def test_clip_exceeds_max_duration(self):
        response = self.client.post('/clip', json={
            'url': 'https://www.youtube.com/watch?v=test',
            'start': 0,
            'end': 200
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(), {'error': 'Max 3 minutes allowed'})

if __name__ == '__main__':
    unittest.main()
