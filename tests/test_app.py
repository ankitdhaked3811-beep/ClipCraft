import unittest
from unittest.mock import patch, MagicMock
import os
import tempfile
import time
from app import app, cleanup_path, temp_cleanups


class TestApp(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_health(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'status': 'ok'})

    def test_info_no_url(self):
        response = self.client.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

    @patch('yt_dlp.YoutubeDL')
    def test_info_success(self, mock_ydl_cls):
        mock_ydl_instance = MagicMock()
        mock_ydl_instance.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'https://example.com/thumb.jpg',
        }
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl_instance

        response = self.client.post('/info', json={'url': 'https://youtube.com/watch?v=123'})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['title'], 'Test Video')
        self.assertEqual(data['duration'], 120)
        self.assertEqual(data['channel'], 'Test Channel')
        self.assertEqual(data['thumbnail'], 'https://example.com/thumb.jpg')

    def test_clip_missing_url(self):
        response = self.client.post('/clip', json={'start': 0, 'end': 30})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

    def test_clip_duration_exceeded(self):
        response = self.client.post('/clip', json={'url': 'https://youtube.com/watch?v=123', 'start': 0, 'end': 190})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(), {'error': 'Max 3 minutes allowed'})

    @patch('yt_dlp.YoutubeDL')
    def test_clip_video_download_success(self, mock_ydl_cls):
        def fake_download(urls):
            # Find the output path created by ydl and write a dummy file
            opts = mock_ydl_cls.call_args[0][0]
            outtmpl = opts['outtmpl']
            with open(outtmpl, 'wb') as f:
                f.write(b'dummy video content')

        mock_ydl_instance = MagicMock()
        mock_ydl_instance.download.side_effect = fake_download
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl_instance

        response = self.client.post('/clip', json={
            'url': 'https://youtube.com/watch?v=123',
            'start': 10,
            'end': 20,
            'format_type': 'video',
            'quality': '720p'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b'dummy video content')
        self.assertIn('clip_10_20.mp4', response.headers.get('Content-Disposition', ''))
        response.close()

    @patch('yt_dlp.YoutubeDL')
    def test_clip_audio_download_success(self, mock_ydl_cls):
        def fake_download(urls):
            opts = mock_ydl_cls.call_args[0][0]
            outtmpl_pattern = opts['outtmpl']
            # outtmpl is like /tmp/.../clip.%(ext)s
            parent_dir = os.path.dirname(outtmpl_pattern)
            mp3_path = os.path.join(parent_dir, 'clip.mp3')
            with open(mp3_path, 'wb') as f:
                f.write(b'dummy audio content')

        mock_ydl_instance = MagicMock()
        mock_ydl_instance.download.side_effect = fake_download
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl_instance

        response = self.client.post('/clip', json={
            'url': 'https://youtube.com/watch?v=123',
            'start': 0,
            'end': 30,
            'format_type': 'audio',
            'quality': '320kbps'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b'dummy audio content')
        self.assertIn('clip_0_30.mp3', response.headers.get('Content-Disposition', ''))
        response.close()

    @patch('yt_dlp.YoutubeDL')
    def test_clip_exception_cleans_tmpdir(self, mock_ydl_cls):
        mock_ydl_instance = MagicMock()
        mock_ydl_instance.download.side_effect = RuntimeError('Download crashed')
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl_instance

        response = self.client.post('/clip', json={
            'url': 'https://youtube.com/watch?v=123',
            'start': 0,
            'end': 10,
        })
        self.assertEqual(response.status_code, 500)
        self.assertIn('Download crashed', response.get_json()['error'])

    def test_cleanup_path(self):
        tmp_dir = tempfile.mkdtemp()
        dummy_file = os.path.join(tmp_dir, 'file.txt')
        with open(dummy_file, 'w') as f:
            f.write('test')

        self.assertTrue(os.path.exists(tmp_dir))
        cleanup_path(tmp_dir, delay=0.05)
        self.assertIn(tmp_dir, temp_cleanups)

        time.sleep(0.2)
        self.assertFalse(os.path.exists(tmp_dir))
        self.assertNotIn(tmp_dir, temp_cleanups)


if __name__ == '__main__':
    unittest.main()
