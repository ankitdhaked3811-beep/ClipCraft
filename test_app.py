import unittest
from unittest.mock import patch
from app import app, fetch_video_info

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        fetch_video_info.cache_clear()

    def test_health(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'status': 'ok'})

    @patch('yt_dlp.YoutubeDL')
    def test_info_endpoint(self, mock_ydl_class):
        mock_ydl_instance = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl_instance.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'https://example.com/thumb.jpg',
        }

        response = self.client.post('/info', json={'url': 'https://www.youtube.com/watch?v=test1234567'})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['title'], 'Test Video')
        self.assertEqual(data['duration'], 120)
        self.assertEqual(data['channel'], 'Test Channel')
        self.assertEqual(data['thumbnail'], 'https://example.com/thumb.jpg')

    @patch('yt_dlp.YoutubeDL')
    def test_info_caching(self, mock_ydl_class):
        mock_ydl_instance = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl_instance.extract_info.return_value = {
            'title': 'Cached Video',
            'duration': 60,
            'uploader': 'Cached Channel',
            'thumbnail': 'https://example.com/cached.jpg',
        }

        url = 'https://www.youtube.com/watch?v=cache_test_123'

        # First request should call yt_dlp.YoutubeDL
        res1 = self.client.post('/info', json={'url': url})
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(mock_ydl_instance.extract_info.call_count, 1)

        # Second request with the same URL should hit the cache and not invoke extract_info again
        res2 = self.client.post('/info', json={'url': url})
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(mock_ydl_instance.extract_info.call_count, 1)

        # Confirm both requests returned identical cached data
        self.assertEqual(res1.get_json(), res2.get_json())

    def test_info_missing_url(self):
        response = self.client.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

if __name__ == '__main__':
    unittest.main()
