import unittest
from unittest.mock import patch, MagicMock


class AppTestCase(unittest.TestCase):
    def setUp(self):
        # Import app here so changes/fixes in app.py can be tested
        import app
        self.app_module = app
        self.client = app.app.test_client()

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
        mock_ydl_cls.return_value.__enter__.return_value = mock_instance
        mock_instance.extract_info.return_value = {
            'title': 'Test Title',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'https://example.com/thumb.jpg',
        }

        # Clear cache before test if it exists
        if hasattr(self.app_module, 'info_cache'):
            self.app_module.info_cache.clear()

        # First request - cache miss
        url = 'https://www.youtube.com/watch?v=mock123'
        response1 = self.client.post('/info', json={'url': url})
        self.assertEqual(response1.status_code, 200)
        data1 = response1.get_json()
        self.assertEqual(data1['title'], 'Test Title')
        self.assertEqual(data1['duration'], 120)
        self.assertEqual(data1['channel'], 'Test Channel')
        self.assertEqual(data1['thumbnail'], 'https://example.com/thumb.jpg')
        self.assertEqual(mock_instance.extract_info.call_count, 1)

        # Second request with same URL - should hit cache (no additional extract_info call)
        response2 = self.client.post('/info', json={'url': url})
        self.assertEqual(response2.status_code, 200)
        data2 = response2.get_json()
        self.assertEqual(data2, data1)
        # Should not have called extract_info again if caching is implemented
        self.assertEqual(mock_instance.extract_info.call_count, 1)

    def test_clip_missing_url(self):
        response = self.client.post('/clip', json={'start': 0, 'end': 30})
        self.assertEqual(response.status_code, 400)
        self.assertIn('URL required', response.get_json().get('error', ''))

    def test_clip_duration_limit(self):
        response = self.client.post('/clip', json={'url': 'https://example.com', 'start': 0, 'end': 200})
        self.assertEqual(response.status_code, 400)
        self.assertIn('Max 3 minutes allowed', response.get_json().get('error', ''))


if __name__ == '__main__':
    unittest.main()
