import unittest
from unittest.mock import patch
import time
import app

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()
        app.fetch_video_info.cache_clear()

    def test_health_check(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'status': 'ok'})

    def test_info_missing_url(self):
        response = self.client.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

    def test_info_caching(self):
        url = "https://www.youtube.com/watch?v=unittest_video_123"
        mock_data = {
            'title': 'Unit Test Video',
            'duration': 120,
            'uploader': 'Test Uploader',
            'thumbnail': 'https://example.com/thumb.jpg',
        }

        call_count = 0

        def mock_extract(self_ydl, extract_url, download=False):
            nonlocal call_count
            call_count += 1
            time.sleep(0.05)  # Simulate network latency
            return mock_data

        with patch.object(app.yt_dlp.YoutubeDL, 'extract_info', mock_extract):
            # First request (uncached)
            start_time = time.perf_counter()
            response1 = self.client.post('/info', json={'url': url})
            duration1 = time.perf_counter() - start_time

            self.assertEqual(response1.status_code, 200)
            json1 = response1.get_json()
            self.assertEqual(json1['title'], 'Unit Test Video')
            self.assertEqual(json1['channel'], 'Test Uploader')

            # Second request (cached)
            start_time = time.perf_counter()
            response2 = self.client.post('/info', json={'url': url})
            duration2 = time.perf_counter() - start_time

            self.assertEqual(response2.status_code, 200)
            json2 = response2.get_json()
            self.assertEqual(json2['title'], 'Unit Test Video')

            # Verify that extract_info was only called ONCE due to caching
            self.assertEqual(call_count, 1)
            # Verify cached request is significantly faster
            self.assertLess(duration2, duration1)

    def test_clip_validations(self):
        # Missing URL
        res1 = self.client.post('/clip', json={'start': 0, 'end': 30})
        self.assertEqual(res1.status_code, 400)

        # Duration exceeding 185s limit
        res2 = self.client.post('/clip', json={'url': 'https://example.com/vid', 'start': 0, 'end': 200})
        self.assertEqual(res2.status_code, 400)
        self.assertIn('Max 3 minutes allowed', res2.get_json()['error'])

if __name__ == '__main__':
    unittest.main()
