import unittest
from unittest.mock import patch, MagicMock
from app import app

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        app.testing = True

    def test_health(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'status': 'ok'})

    def test_info_missing_url(self):
        response = self.client.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)

    @patch('yt_dlp.YoutubeDL')
    def test_info_success_and_noplaylist_option(self, mock_youtube_dl):
        mock_ydl_instance = MagicMock()
        mock_ydl_instance.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 120,
            'uploader': 'Test Channel',
            'thumbnail': 'https://example.com/thumb.jpg'
        }
        mock_youtube_dl.return_value.__enter__.return_value = mock_ydl_instance

        url = 'https://www.youtube.com/watch?v=abc12345&list=PL12345'
        response = self.client.post('/info', json={'url': url})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {
            'title': 'Test Video',
            'duration': 120,
            'channel': 'Test Channel',
            'thumbnail': 'https://example.com/thumb.jpg'
        })

        # Ensure yt_dlp.YoutubeDL was initialized with 'noplaylist': True
        mock_youtube_dl.assert_called_once()
        opts = mock_youtube_dl.call_args[0][0]
        self.assertTrue(opts.get('noplaylist'), "Expected 'noplaylist' option to be True in ydl_opts")

    def test_clip_exceeds_max_duration(self):
        response = self.client.post('/clip', json={
            'url': 'https://www.youtube.com/watch?v=abc12345',
            'start': 0,
            'end': 200
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {'error': 'Max 3 minutes allowed'})

if __name__ == '__main__':
    unittest.main()
