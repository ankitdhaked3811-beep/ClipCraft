import os
import unittest
from unittest.mock import patch, MagicMock
from app import app, fetch_video_info

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        fetch_video_info.cache_clear()

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
        mock_ydl_instance = MagicMock()
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl_instance
        mock_ydl_instance.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'https://example.com/thumb.jpg',
        }

        url = 'https://youtube.com/watch?v=12345'

        # First call
        res1 = self.client.post('/info', json={'url': url})
        self.assertEqual(res1.status_code, 200)
        data1 = res1.get_json()
        self.assertEqual(data1['title'], 'Test Video')
        self.assertEqual(data1['duration'], 120)
        self.assertEqual(data1['channel'], 'Test Channel')
        self.assertEqual(data1['thumbnail'], 'https://example.com/thumb.jpg')
        self.assertEqual(mock_ydl_instance.extract_info.call_count, 1)

        # Second call (cached)
        res2 = self.client.post('/info', json={'url': url})
        self.assertEqual(res2.status_code, 200)
        data2 = res2.get_json()
        self.assertEqual(data2, data1)
        # Verify extract_info was not called again
        self.assertEqual(mock_ydl_instance.extract_info.call_count, 1)

    def test_clip_endpoint_missing_url(self):
        response = self.client.post('/clip', json={})
        self.assertEqual(response.status_code, 400)

    def test_clip_endpoint_exceeds_max_duration(self):
        response = self.client.post('/clip', json={'url': 'https://youtube.com/watch?v=123', 'start': 0, 'end': 200})
        self.assertEqual(response.status_code, 400)
        self.assertIn('Max 3 minutes allowed', response.get_json()['error'])

    @patch('yt_dlp.YoutubeDL')
    def test_clip_endpoint_video_success(self, mock_ydl_cls):
        mock_ydl_instance = MagicMock()
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl_instance

        def side_effect(urls):
            # Create dummy clip.mp4 file in outtmpl target directory if requested
            call_args = mock_ydl_cls.call_args[0][0]
            out_path = call_args.get('outtmpl')
            if out_path:
                with open(out_path, 'wb') as f:
                    f.write(b'dummy video content')

        mock_ydl_instance.download.side_effect = side_effect

        response = self.client.post('/clip', json={'url': 'https://youtube.com/watch?v=123', 'start': 0, 'end': 10, 'format_type': 'video'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'video/mp4')

if __name__ == '__main__':
    unittest.main()
