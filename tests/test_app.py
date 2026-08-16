import unittest
from unittest.mock import patch, MagicMock
import os
import tempfile
from app import app

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_health(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'status': 'ok'})

    def test_info_missing_url(self):
        response = self.client.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

    @patch('yt_dlp.YoutubeDL')
    def test_info_success(self, mock_ydl_cls):
        mock_ydl_instance = MagicMock()
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl_instance
        mock_ydl_instance.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'http://example.com/thumb.jpg',
        }

        response = self.client.post('/info', json={'url': 'https://www.youtube.com/watch?v=12345'})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['title'], 'Test Video')
        self.assertEqual(data['duration'], 120)
        self.assertEqual(data['channel'], 'Test Channel')

        # Verify yt_dlp was called with noplaylist=True
        mock_ydl_cls.assert_called_once()
        opts = mock_ydl_cls.call_args[0][0]
        self.assertTrue(opts.get('noplaylist'))

    def test_clip_exceeds_max_duration(self):
        response = self.client.post('/clip', json={
            'url': 'https://www.youtube.com/watch?v=12345',
            'start': 0,
            'end': 200
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(), {'error': 'Max 3 minutes allowed'})

    @patch('yt_dlp.YoutubeDL')
    def test_clip_video_success(self, mock_ydl_cls):
        mock_ydl_instance = MagicMock()
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl_instance

        # Create dummy file when ydl.download is called
        def side_effect(urls):
            opts = mock_ydl_cls.call_args[0][0]
            outtmpl = opts.get('outtmpl')
            with open(outtmpl, 'w') as f:
                f.write('dummy video content')

        mock_ydl_instance.download.side_effect = side_effect

        response = self.client.post('/clip', json={
            'url': 'https://www.youtube.com/watch?v=12345',
            'start': 0,
            'end': 30,
            'format_type': 'video',
            'quality': '720p'
        })

        self.assertEqual(response.status_code, 200)
        opts = mock_ydl_cls.call_args[0][0]
        self.assertTrue(opts.get('noplaylist'))

    @patch('yt_dlp.YoutubeDL')
    def test_clip_audio_success(self, mock_ydl_cls):
        mock_ydl_instance = MagicMock()
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl_instance

        def side_effect(urls):
            opts = mock_ydl_cls.call_args[0][0]
            outtmpl = opts.get('outtmpl')
            # outtmpl is tmpdir/clip.%(ext)s
            target = outtmpl.replace('%(ext)s', 'mp3')
            with open(target, 'w') as f:
                f.write('dummy audio content')

        mock_ydl_instance.download.side_effect = side_effect

        response = self.client.post('/clip', json={
            'url': 'https://www.youtube.com/watch?v=12345',
            'start': 0,
            'end': 30,
            'format_type': 'audio',
            'quality': '128kbps'
        })

        self.assertEqual(response.status_code, 200)
        opts = mock_ydl_cls.call_args[0][0]
        self.assertTrue(opts.get('noplaylist'))

if __name__ == '__main__':
    unittest.main()
