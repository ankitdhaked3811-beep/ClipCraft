import unittest
from unittest.mock import patch, MagicMock
import time
import json
import os
import tempfile
from app import app, _fetch_info

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        _fetch_info.cache_clear()

    def test_health_endpoint(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'status': 'ok'})

    def test_info_endpoint_missing_url(self):
        response = self.client.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

    @patch('yt_dlp.YoutubeDL')
    def test_info_endpoint_success_and_caching(self, mock_ydl_cls):
        mock_ydl = MagicMock()
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = {
            'title': 'Sample Video',
            'duration': 180,
            'uploader': 'Sample Channel',
            'thumbnail': 'https://example.com/thumb.jpg'
        }

        # First request - cache miss
        url = 'https://example.com/watch?v=cache_test'
        response1 = self.client.post('/info', json={'url': url})
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(mock_ydl.extract_info.call_count, 1)

        # Second request - cache hit
        response2 = self.client.post('/info', json={'url': url})
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.get_json(), response1.get_json())
        # YoutubeDL extract_info should NOT have been called again
        self.assertEqual(mock_ydl.extract_info.call_count, 1)

        # Check ydl_opts passed to YoutubeDL includes noplaylist
        ydl_opts = mock_ydl_cls.call_args[0][0]
        self.assertTrue(ydl_opts.get('noplaylist'))

    def test_clip_endpoint_missing_url(self):
        response = self.client.post('/clip', json={})
        self.assertEqual(response.status_code, 400)

    def test_clip_endpoint_exceeds_max_duration(self):
        response = self.client.post('/clip', json={
            'url': 'https://example.com/watch?v=test',
            'start': 0,
            'end': 200
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('Max 3 minutes allowed', response.get_json()['error'])

if __name__ == '__main__':
    unittest.main()
