import os
import time
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from app import app, _extract_info_cached, cleanup_file, temp_files

class ClipCraftAppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        _extract_info_cached.cache_clear()

    def test_health_endpoint(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'status': 'ok'})

    def test_info_missing_url(self):
        response = self.client.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

    @patch('yt_dlp.YoutubeDL')
    def test_info_success_and_caching(self, mock_ydl_class):
        mock_ydl_instance = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
        mock_ydl_instance.extract_info.return_value = {
            'title': 'Sample Video',
            'duration': 120,
            'uploader': 'Sample Channel',
            'thumbnail': 'https://example.com/thumb.jpg',
        }

        url = 'https://www.youtube.com/watch?v=sample123'

        # First request - cache miss
        res1 = self.client.post('/info', json={'url': url})
        self.assertEqual(res1.status_code, 200)
        json1 = res1.get_json()
        self.assertEqual(json1['title'], 'Sample Video')
        self.assertEqual(json1['duration'], 120)

        # Second request - cache hit
        res2 = self.client.post('/info', json={'url': url})
        self.assertEqual(res2.status_code, 200)

        # Verify YoutubeDL extract_info was only called ONCE due to caching
        self.assertEqual(mock_ydl_instance.extract_info.call_count, 1)

    @patch('yt_dlp.YoutubeDL')
    def test_info_exception_handling(self, mock_ydl_class):
        mock_ydl_instance = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
        mock_ydl_instance.extract_info.side_effect = Exception("Extraction failed")

        res = self.client.post('/info', json={'url': 'https://example.com/invalid'})
        self.assertEqual(res.status_code, 500)
        self.assertEqual(res.get_json(), {'error': 'Extraction failed'})

    def test_clip_missing_url(self):
        res = self.client.post('/clip', json={})
        self.assertEqual(res.status_code, 400)

    def test_clip_exceeds_max_duration(self):
        res = self.client.post('/clip', json={'url': 'https://example.com/v', 'start': 0, 'end': 200})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.get_json(), {'error': 'Max 3 minutes allowed'})

    @patch('yt_dlp.YoutubeDL')
    def test_clip_video_success(self, mock_ydl_class):
        mock_ydl_instance = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance

        def side_effect_download(urls):
            # Create the expected file when download is called
            opts = mock_ydl_class.call_args[0][0] if mock_ydl_class.call_args[0] else mock_ydl_class.call_args[1]
            out_path = opts.get('outtmpl') if isinstance(opts, dict) else None
            if out_path:
                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                with open(out_path, 'wb') as f:
                    f.write(b'video content')

        mock_ydl_instance.download.side_effect = side_effect_download

        res = self.client.post('/clip', json={
            'url': 'https://example.com/video',
            'start': 10,
            'end': 30,
            'format_type': 'video',
            'quality': '720p'
        })
        self.assertEqual(res.status_code, 200)

    def test_cleanup_file_removes_file_and_empty_dir(self):
        tmpdir = tempfile.mkdtemp()
        test_file = os.path.join(tmpdir, 'test.mp4')
        with open(test_file, 'w') as f:
            f.write('data')

        temp_files[test_file] = True
        cleanup_file(test_file, delay=0.01)
        time.sleep(0.05)

        self.assertFalse(os.path.exists(test_file))
        self.assertFalse(os.path.exists(tmpdir))

if __name__ == '__main__':
    unittest.main()
