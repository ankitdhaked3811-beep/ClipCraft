import unittest
from unittest.mock import patch, MagicMock
import os
import shutil

class TestApp(unittest.TestCase):
    def setUp(self):
        from app import app
        self.app = app
        self.client = app.test_client()

    def test_health_endpoint(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'status': 'ok'})

    def test_info_missing_url(self):
        response = self.client.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

    @patch('yt_dlp.YoutubeDL')
    def test_info_cached_extraction(self, mock_ydl_cls):
        mock_ydl_instance = MagicMock()
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl_instance
        mock_ydl_instance.extract_info.return_value = {
            'title': 'Test Video Title',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'https://example.com/thumb.jpg'
        }

        url = "https://www.youtube.com/watch?v=mock_test_123"

        # First request should invoke YoutubeDL
        res1 = self.client.post('/info', json={'url': url})
        self.assertEqual(res1.status_code, 200)
        json1 = res1.get_json()
        self.assertEqual(json1['title'], 'Test Video Title')
        self.assertEqual(json1['duration'], 120)

        call_count_after_first = mock_ydl_cls.call_count

        # Second request for same URL should hit cache without calling YoutubeDL again
        res2 = self.client.post('/info', json={'url': url})
        self.assertEqual(res2.status_code, 200)
        json2 = res2.get_json()
        self.assertEqual(json2, json1)

        self.assertEqual(mock_ydl_cls.call_count, call_count_after_first)

    def test_clip_missing_url(self):
        response = self.client.post('/clip', json={})
        self.assertEqual(response.status_code, 400)

    def test_clip_exceeds_max_duration(self):
        response = self.client.post('/clip', json={'url': 'https://example.com', 'start': 0, 'end': 200})
        self.assertEqual(response.status_code, 400)
        self.assertIn('Max 3 minutes allowed', response.get_json().get('error', ''))

if __name__ == '__main__':
    unittest.main()
