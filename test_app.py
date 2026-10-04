import unittest
from unittest.mock import patch
import os
import tempfile
import time

import app

class AppTestCase(unittest.TestCase):
    def setUp(self):
        app.app.testing = True
        self.client = app.app.test_client()
        app._fetch_video_info.cache_clear()

    def test_health_endpoint(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'status': 'ok'})

    def test_info_endpoint_missing_url(self):
        response = self.client.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

    @patch('app.yt_dlp.YoutubeDL')
    def test_info_endpoint_caching(self, mock_ydl):
        mock_instance = mock_ydl.return_value.__enter__.return_value
        mock_instance.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'http://example.com/thumb.jpg',
        }

        url = 'https://example.com/watch?v=123'

        # First request
        res1 = self.client.post('/info', json={'url': url})
        self.assertEqual(res1.status_code, 200)
        data1 = res1.get_json()
        self.assertEqual(data1['title'], 'Test Video')
        self.assertEqual(mock_instance.extract_info.call_count, 1)

        # Second request (should hit cache)
        res2 = self.client.post('/info', json={'url': url})
        self.assertEqual(res2.status_code, 200)
        data2 = res2.get_json()
        self.assertEqual(data2['title'], 'Test Video')
        self.assertEqual(mock_instance.extract_info.call_count, 1) # Still 1 because cached

    def test_clip_missing_url(self):
        response = self.client.post('/clip', json={})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(), {'error': 'URL required'})

    def test_clip_exceeds_max_duration(self):
        response = self.client.post('/clip', json={
            'url': 'https://example.com/watch?v=123',
            'start': 0,
            'end': 200
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(), {'error': 'Max 3 minutes allowed'})

    def test_cleanup_file(self):
        tmpdir = tempfile.mkdtemp()
        dummy_file = os.path.join(tmpdir, 'clip.mp4')
        with open(dummy_file, 'w') as f:
            f.write('data')

        app.temp_files[dummy_file] = True
        app.cleanup_file(dummy_file, delay=0.05)
        time.sleep(0.15)

        self.assertFalse(os.path.exists(tmpdir))
        self.assertNotIn(dummy_file, app.temp_files)

if __name__ == '__main__':
    unittest.main()
