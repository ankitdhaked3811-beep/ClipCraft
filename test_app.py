import unittest
from unittest.mock import patch, MagicMock
import os
import shutil
import time
from app import app, temp_files, fetch_video_info, cleanup_file

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        fetch_video_info.cache_clear()

    def test_health(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'status': 'ok'})

    @patch('yt_dlp.YoutubeDL')
    def test_info(self, mock_ydl_class):
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'https://example.com/thumb.jpg'
        }

        url = 'https://www.youtube.com/watch?v=test'
        response = self.client.post('/info', json={'url': url})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {
            'title': 'Test Video',
            'duration': 120,
            'channel': 'Test Channel',
            'thumbnail': 'https://example.com/thumb.jpg'
        })

        # Verify noplaylist=True was passed in ydl_opts
        mock_ydl_class.assert_called_once()
        opts = mock_ydl_class.call_args[0][0]
        self.assertTrue(opts.get('noplaylist'))

        # Verify caching: second call for same URL should return cached result without YoutubeDL instantiation
        mock_ydl_class.reset_mock()
        response_cached = self.client.post('/info', json={'url': url})
        self.assertEqual(response_cached.status_code, 200)
        mock_ydl_class.assert_not_called()

    def test_info_no_url(self):
        response = self.client.post('/info', json={})
        self.assertEqual(response.status_code, 400)

    @patch('yt_dlp.YoutubeDL')
    def test_clip_video(self, mock_ydl_class):
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        def mock_download(urls):
            opts = mock_ydl_class.call_args[0][0]
            outtmpl = opts.get('outtmpl')
            with open(outtmpl, 'wb') as f:
                f.write(b'fake mp4 data')

        mock_ydl.download.side_effect = mock_download

        response = self.client.post('/clip', json={
            'url': 'https://www.youtube.com/watch?v=test',
            'start': 0,
            'end': 10,
            'format_type': 'video',
            'quality': '720p'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'video/mp4')

        # Verify noplaylist=True in ydl_opts
        opts = mock_ydl_class.call_args[0][0]
        self.assertTrue(opts.get('noplaylist'))

    @patch('yt_dlp.YoutubeDL')
    def test_clip_audio(self, mock_ydl_class):
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        def mock_download(urls):
            opts = mock_ydl_class.call_args[0][0]
            outtmpl = opts.get('outtmpl')
            out_dir = os.path.dirname(outtmpl)
            audio_file = os.path.join(out_dir, 'clip.mp3')
            with open(audio_file, 'wb') as f:
                f.write(b'fake mp3 data')

        mock_ydl.download.side_effect = mock_download

        response = self.client.post('/clip', json={
            'url': 'https://www.youtube.com/watch?v=test',
            'start': 0,
            'end': 10,
            'format_type': 'audio',
            'quality': '320kbps'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'audio/mpeg')
        opts = mock_ydl_class.call_args[0][0]
        self.assertTrue(opts.get('noplaylist'))

    def test_cleanup_file(self):
        import tempfile
        tmpdir = tempfile.mkdtemp()
        file_path = os.path.join(tmpdir, 'clip.mp4')
        with open(file_path, 'w') as f:
            f.write('test')

        temp_files[file_path] = True
        cleanup_file(file_path, delay=0.1)
        time.sleep(0.3)

        self.assertFalse(os.path.exists(tmpdir))
        self.assertNotIn(file_path, temp_files)

if __name__ == '__main__':
    unittest.main()
