import unittest
from unittest.mock import patch
import os
import tempfile
import time
from app import app, _fetch_info

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        # Clear lru_cache before each test
        _fetch_info.cache_clear()

    def test_health(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'status': 'ok'})

    def test_info_missing_url(self):
        response = self.client.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

    @patch('yt_dlp.YoutubeDL')
    def test_info_success_and_caching(self, mock_ydl_class):
        mock_instance = mock_ydl_class.return_value.__enter__.return_value
        mock_instance.extract_info.return_value = {
            'title': 'Test Title',
            'duration': 100,
            'uploader': 'Test Uploader',
            'thumbnail': 'https://example.com/thumb.jpg'
        }

        url = 'https://www.youtube.com/watch?v=mock123'

        # First call
        res1 = self.client.post('/info', json={'url': url})
        self.assertEqual(res1.status_code, 200)
        json1 = res1.get_json()
        self.assertEqual(json1['title'], 'Test Title')
        self.assertEqual(json1['duration'], 100)
        self.assertEqual(json1['channel'], 'Test Uploader')
        self.assertEqual(json1['thumbnail'], 'https://example.com/thumb.jpg')

        # Verify extract_info was called once
        mock_instance.extract_info.assert_called_once_with(url, download=False)

        # Second call (should be served from LRU cache)
        res2 = self.client.post('/info', json={'url': url})
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.get_json(), json1)

        # Confirm extract_info was NOT called a second time
        self.assertEqual(mock_instance.extract_info.call_count, 1)

    def test_clip_missing_url(self):
        response = self.client.post('/clip', json={})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(), {'error': 'URL required'})

    def test_clip_exceeds_max_duration(self):
        response = self.client.post('/clip', json={
            'url': 'https://www.youtube.com/watch?v=mock123',
            'start': 0,
            'end': 200
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(), {'error': 'Max 3 minutes allowed'})

if __name__ == '__main__':
    unittest.main()
