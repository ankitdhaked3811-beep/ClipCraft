import unittest
import time
from unittest.mock import patch, MagicMock
from app import app, extract_video_info

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        extract_video_info.cache_clear()

    def test_health(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'status': 'ok'})

    def test_info_missing_url(self):
        response = self.client.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)

    @patch('yt_dlp.YoutubeDL')
    def test_info_success_and_caching(self, mock_ydl):
        mock_instance = MagicMock()
        mock_ydl.return_value.__enter__.return_value = mock_instance

        def slow_extract(url, download=False):
            time.sleep(0.05)  # Simulate network latency
            return {
                'title': 'Test Video',
                'duration': 120,
                'uploader': 'Test Channel',
                'thumbnail': 'https://example.com/thumb.jpg'
            }

        mock_instance.extract_info.side_effect = slow_extract
        test_url = 'https://example.com/watch?v=123'

        # First request - cache miss (simulates slow network call)
        t0 = time.time()
        response1 = self.client.post('/info', json={'url': test_url})
        t1 = time.time()
        duration_miss = t1 - t0

        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response1.json, {
            'title': 'Test Video',
            'duration': 120,
            'channel': 'Test Channel',
            'thumbnail': 'https://example.com/thumb.jpg'
        })
        self.assertEqual(mock_instance.extract_info.call_count, 1)

        # Verify noplaylist is set in YoutubeDL options
        mock_ydl.assert_called_with({
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'noplaylist': True,
        })

        # Second request with same URL - cache hit (<1ms)
        t0 = time.time()
        response2 = self.client.post('/info', json={'url': test_url})
        t1 = time.time()
        duration_hit = t1 - t0

        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.json, response1.json)
        # extract_info should NOT be called a second time due to LRU cache
        self.assertEqual(mock_instance.extract_info.call_count, 1)

        # Confirm hit is significantly faster than miss
        self.assertLess(duration_hit, duration_miss)

    def test_clip_missing_url(self):
        response = self.client.post('/clip', json={})
        self.assertEqual(response.status_code, 400)

    def test_clip_exceeds_max_duration(self):
        response = self.client.post('/clip', json={'url': 'http://example.com', 'start': 0, 'end': 200})
        self.assertEqual(response.status_code, 400)
        self.assertIn('Max 3 minutes allowed', response.json['error'])

if __name__ == '__main__':
    unittest.main()
