import unittest
from unittest.mock import patch, MagicMock
import json
import os
import tempfile
import time
from app import app, INFO_CACHE

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        INFO_CACHE.clear()

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
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {
            'title': 'Test Title',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'https://example.com/thumb.jpg'
        }
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

        url = 'https://www.youtube.com/watch?v=test'
        # First call: hits yt_dlp
        response1 = self.client.post('/info', json={'url': url})
        self.assertEqual(response1.status_code, 200)
        data1 = response1.get_json()
        self.assertEqual(data1['title'], 'Test Title')
        self.assertEqual(mock_ydl.extract_info.call_count, 1)

        # Second call: hits cache, yt_dlp is not called again
        response2 = self.client.post('/info', json={'url': url})
        self.assertEqual(response2.status_code, 200)
        data2 = response2.get_json()
        self.assertEqual(data2, data1)
        self.assertEqual(mock_ydl.extract_info.call_count, 1)

    def test_clip_missing_url(self):
        response = self.client.post('/clip', json={})
        self.assertEqual(response.status_code, 400)

    def test_clip_duration_exceeded(self):
        response = self.client.post('/clip', json={'url': 'https://www.youtube.com/watch?v=test', 'start': 0, 'end': 200})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(), {'error': 'Max 3 minutes allowed'})

if __name__ == '__main__':
    unittest.main()
