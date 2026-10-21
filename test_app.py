import unittest
from unittest.mock import patch, MagicMock
from app import app, fetch_video_info

class TestApp(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        fetch_video_info.cache_clear()

    def test_health(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'status': 'ok'})

    def test_info_missing_url(self):
        response = self.client.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)

    @patch('app.yt_dlp.YoutubeDL')
    def test_info_success_and_caching(self, mock_yt):
        mock_ydl_instance = MagicMock()
        mock_yt.return_value.__enter__.return_value = mock_ydl_instance
        mock_ydl_instance.extract_info.return_value = {
            'title': 'Test Title',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'https://example.com/thumb.jpg',
        }

        url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'

        # First request - cache miss, YoutubeDL called
        res1 = self.client.post('/info', json={'url': url})
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res1.json['title'], 'Test Title')
        self.assertEqual(mock_ydl_instance.extract_info.call_count, 1)

        cache_info1 = fetch_video_info.cache_info()
        self.assertEqual(cache_info1.hits, 0)
        self.assertEqual(cache_info1.misses, 1)

        # Second request with same URL - cache hit, YoutubeDL not called again
        res2 = self.client.post('/info', json={'url': url})
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json['title'], 'Test Title')
        self.assertEqual(mock_ydl_instance.extract_info.call_count, 1)

        cache_info2 = fetch_video_info.cache_info()
        self.assertEqual(cache_info2.hits, 1)
        self.assertEqual(cache_info2.misses, 1)

if __name__ == '__main__':
    unittest.main()
