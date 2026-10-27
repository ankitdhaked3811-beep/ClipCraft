import unittest
from unittest.mock import patch
import os
import json
from app import app, fetch_video_info

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        fetch_video_info.cache_clear()

    def test_health(self):
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'status': 'ok'})

    def test_info_missing_url(self):
        response = self.app.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)

    @patch('app.yt_dlp.YoutubeDL')
    def test_info_success_and_caching(self, mock_ydl):
        mock_instance = mock_ydl.return_value.__enter__.return_value
        mock_instance.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'http://example.com/thumb.jpg'
        }

        # First request
        res1 = self.app.post('/info', json={'url': 'http://example.com/video'})
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res1.json['title'], 'Test Video')
        self.assertEqual(res1.json['duration'], 120)

        # Second request (should hit LRU cache, so yt_dlp is not called again)
        res2 = self.app.post('/info', json={'url': 'http://example.com/video'})
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json['title'], 'Test Video')

        # Assert YoutubeDL extract_info was called only once due to caching
        self.assertEqual(mock_instance.extract_info.call_count, 1)

    def test_clip_missing_url(self):
        response = self.app.post('/clip', json={})
        self.assertEqual(response.status_code, 400)

    def test_clip_duration_exceeded(self):
        response = self.app.post('/clip', json={'url': 'http://example.com', 'start': 0, 'end': 200})
        self.assertEqual(response.status_code, 400)
        self.assertIn('Max 3 minutes allowed', response.json['error'])

if __name__ == '__main__':
    unittest.main()
