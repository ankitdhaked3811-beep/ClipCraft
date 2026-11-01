import unittest
from unittest.mock import patch, MagicMock
from app import app, _get_video_info

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        _get_video_info.cache_clear()

    def test_health(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'status': 'ok'})

    def test_info_missing_url(self):
        response = self.client.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

    @patch('yt_dlp.YoutubeDL')
    def test_info_success_and_caching(self, mock_ydl_cls):
        mock_instance = MagicMock()
        mock_instance.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'http://example.com/thumb.jpg',
        }
        mock_ydl_cls.return_value.__enter__.return_value = mock_instance

        test_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'

        # First call: cache miss, extracts from yt_dlp
        response1 = self.client.post('/info', json={'url': test_url})
        self.assertEqual(response1.status_code, 200)
        data1 = response1.get_json()
        self.assertEqual(data1['title'], 'Test Video')
        self.assertEqual(data1['duration'], 120)
        self.assertEqual(data1['channel'], 'Test Channel')
        self.assertEqual(data1['thumbnail'], 'http://example.com/thumb.jpg')
        self.assertEqual(mock_instance.extract_info.call_count, 1)

        # Second call: cache hit, yt_dlp extract_info not called again
        response2 = self.client.post('/info', json={'url': test_url})
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.get_json(), data1)
        self.assertEqual(mock_instance.extract_info.call_count, 1)

    @patch('yt_dlp.YoutubeDL')
    def test_info_exception(self, mock_ydl_cls):
        mock_instance = MagicMock()
        mock_instance.extract_info.side_effect = Exception("Extraction failed")
        mock_ydl_cls.return_value.__enter__.return_value = mock_instance

        response = self.client.post('/info', json={'url': 'https://www.youtube.com/watch?v=error'})
        self.assertEqual(response.status_code, 500)
        self.assertIn('Extraction failed', response.get_json()['error'])

    def test_clip_validation(self):
        # Missing URL
        response = self.client.post('/clip', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('URL required', response.get_json()['error'])

        # Exceeds 185s
        response = self.client.post('/clip', json={'url': 'https://example.com', 'start': 0, 'end': 200})
        self.assertEqual(response.status_code, 400)
        self.assertIn('Max 3 minutes allowed', response.get_json()['error'])

if __name__ == '__main__':
    unittest.main()
