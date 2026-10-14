import unittest
from unittest.mock import patch, MagicMock
import os
import shutil
import tempfile
from app import app, _extract_video_info

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_health(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'status': 'ok'})

    def test_info_missing_url(self):
        response = self.client.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())
        self.assertEqual(response.get_json()['error'], 'URL required')

    @patch('app._extract_video_info')
    def test_info_success_and_caching(self, mock_extract):
        mock_extract.return_value = {
            'title': 'Test Video',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'https://example.com/thumb.jpg'
        }

        url = 'https://example.com/watch?v=12345'
        response1 = self.client.post('/info', json={'url': url})
        self.assertEqual(response1.status_code, 200)
        json_data1 = response1.get_json()
        self.assertEqual(json_data1['title'], 'Test Video')
        self.assertEqual(json_data1['duration'], 120)
        self.assertEqual(json_data1['channel'], 'Test Channel')
        self.assertEqual(json_data1['thumbnail'], 'https://example.com/thumb.jpg')

        # Clear cache for isolated testing of actual function
        _extract_video_info.cache_clear()

    @patch('yt_dlp.YoutubeDL')
    def test_lru_cache_behavior(self, mock_ydl_cls):
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {
            'title': 'Cached Title',
            'duration': 60,
            'uploader': 'Cached Uploader',
            'thumbnail': 'https://example.com/thumb.jpg'
        }
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

        _extract_video_info.cache_clear()

        url = 'https://example.com/watch?v=cache_test'

        # First call should invoke yt_dlp
        info1 = _extract_video_info(url)
        self.assertEqual(info1['title'], 'Cached Title')
        self.assertEqual(mock_ydl.extract_info.call_count, 1)

        # Second call should use LRU cache without calling extract_info again
        info2 = _extract_video_info(url)
        self.assertEqual(info2['title'], 'Cached Title')
        self.assertEqual(mock_ydl.extract_info.call_count, 1)

    def test_clip_missing_url(self):
        response = self.client.post('/clip', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())
        self.assertEqual(response.get_json()['error'], 'URL required')

    def test_clip_duration_exceeded(self):
        response = self.client.post('/clip', json={
            'url': 'https://example.com/video',
            'start': 0,
            'end': 200
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()['error'], 'Max 3 minutes allowed')

    @patch('yt_dlp.YoutubeDL')
    def test_clip_video_success(self, mock_ydl_cls):
        mock_ydl = MagicMock()
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

        def create_dummy_mp4(urls):
            # simulate ydl creating output file
            args, kwargs = mock_ydl_cls.call_args
            opts = args[0] if args else kwargs.get('params', {})
            out_path = opts.get('outtmpl')
            if out_path:
                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                with open(out_path, 'wb') as f:
                    f.write(b'dummy mp4 data')

        mock_ydl.download.side_effect = create_dummy_mp4

        response = self.client.post('/clip', json={
            'url': 'https://example.com/video',
            'start': 0,
            'end': 30,
            'format_type': 'video',
            'quality': '720p'
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'video/mp4')
        self.assertEqual(response.data, b'dummy mp4 data')

if __name__ == '__main__':
    unittest.main()
