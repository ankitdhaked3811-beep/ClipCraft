import unittest
from unittest.mock import patch, MagicMock
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
        self.assertEqual(response.get_json(), {'error': 'URL required'})

    @patch('yt_dlp.YoutubeDL')
    def test_info_success_and_caching(self, mock_ydl_class):
        mock_instance = MagicMock()
        mock_instance.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'https://example.com/thumb.jpg',
        }
        mock_ydl_class.return_value.__enter__.return_value = mock_instance

        # First request - cache miss
        response1 = self.client.post('/info', json={'url': 'https://example.com/watch?v=123'})
        self.assertEqual(response1.status_code, 200)
        data1 = response1.get_json()
        self.assertEqual(data1['title'], 'Test Video')
        self.assertEqual(data1['duration'], 120)
        self.assertEqual(data1['channel'], 'Test Channel')
        self.assertEqual(data1['thumbnail'], 'https://example.com/thumb.jpg')
        self.assertEqual(mock_instance.extract_info.call_count, 1)

        # Second request - cache hit, should not invoke ydl.extract_info again
        response2 = self.client.post('/info', json={'url': 'https://example.com/watch?v=123'})
        self.assertEqual(response2.status_code, 200)
        data2 = response2.get_json()
        self.assertEqual(data2, data1)
        self.assertEqual(mock_instance.extract_info.call_count, 1)

    @patch('yt_dlp.YoutubeDL')
    def test_info_extraction_error(self, mock_ydl_class):
        mock_instance = MagicMock()
        mock_instance.extract_info.side_effect = RuntimeError('Extraction failed')
        mock_ydl_class.return_value.__enter__.return_value = mock_instance

        response = self.client.post('/info', json={'url': 'https://example.com/watch?v=error'})
        self.assertEqual(response.status_code, 500)
        self.assertIn('Extraction failed', response.get_json()['error'])

    def test_clip_missing_url(self):
        response = self.client.post('/clip', json={})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(), {'error': 'URL required'})

    def test_clip_duration_exceeded(self):
        response = self.client.post('/clip', json={'url': 'https://example.com/watch?v=123', 'start': 0, 'end': 200})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(), {'error': 'Max 3 minutes allowed'})

if __name__ == '__main__':
    unittest.main()
