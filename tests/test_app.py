import unittest
from unittest.mock import MagicMock, patch
from app import app, fetch_video_info

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        fetch_video_info.cache_clear()

    def test_health(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'status': 'ok'})

    def test_info_missing_url(self):
        response = self.client.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('URL required', response.get_json().get('error', ''))

    @patch('yt_dlp.YoutubeDL')
    def test_info_success_and_caching(self, mock_ydl_cls):
        mock_instance = MagicMock()
        mock_instance.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'https://example.com/thumb.jpg',
        }
        mock_ydl_cls.return_value.__enter__.return_value = mock_instance

        url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'

        # First request: fetches metadata via yt_dlp
        response1 = self.client.post('/info', json={'url': url})
        self.assertEqual(response1.status_code, 200)
        data1 = response1.get_json()
        self.assertEqual(data1['title'], 'Test Video')
        self.assertEqual(data1['duration'], 120)
        self.assertEqual(data1['channel'], 'Test Channel')
        self.assertEqual(data1['thumbnail'], 'https://example.com/thumb.jpg')
        self.assertEqual(mock_instance.extract_info.call_count, 1)

        # Second request: served directly from LRU cache
        response2 = self.client.post('/info', json={'url': url})
        self.assertEqual(response2.status_code, 200)
        data2 = response2.get_json()
        self.assertEqual(data2, data1)
        # Verify extract_info was not called again
        self.assertEqual(mock_instance.extract_info.call_count, 1)

    def test_clip_missing_url(self):
        response = self.client.post('/clip', json={'start': 0, 'end': 30})
        self.assertEqual(response.status_code, 400)
        self.assertIn('URL required', response.get_json().get('error', ''))

    def test_clip_exceeds_max_duration(self):
        response = self.client.post('/clip', json={
            'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'start': 0,
            'end': 200,
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('Max 3 minutes allowed', response.get_json().get('error', ''))

if __name__ == '__main__':
    unittest.main()
