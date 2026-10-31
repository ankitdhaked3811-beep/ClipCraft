import unittest
from unittest.mock import patch, MagicMock
from app import app, extract_video_info


class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        # Clear the lru_cache before each test to ensure test isolation
        extract_video_info.cache_clear()

    def test_health_endpoint(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'status': 'ok'})

    def test_info_endpoint_missing_url(self):
        response = self.client.post('/info', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

    @patch('yt_dlp.YoutubeDL')
    def test_info_endpoint_caching(self, mock_ydl_cls):
        mock_ydl_instance = MagicMock()
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl_instance
        mock_ydl_instance.extract_info.return_value = {
            'title': 'Test Clip',
            'duration': 120,
            'uploader': 'Test Creator',
            'thumbnail': 'https://example.com/thumb.jpg',
        }

        url = 'https://www.youtube.com/watch?v=mock_video_id'

        # First request: should call YoutubeDL.extract_info
        res1 = self.client.post('/info', json={'url': url})
        self.assertEqual(res1.status_code, 200)
        data1 = res1.get_json()
        self.assertEqual(data1['title'], 'Test Clip')
        self.assertEqual(mock_ydl_instance.extract_info.call_count, 1)

        # Second request with the same URL: should hit cache and NOT invoke YoutubeDL
        res2 = self.client.post('/info', json={'url': url})
        self.assertEqual(res2.status_code, 200)
        data2 = res2.get_json()
        self.assertEqual(data2, data1)
        # Call count remains 1 due to LRU cache hit
        self.assertEqual(mock_ydl_instance.extract_info.call_count, 1)

        cache_info = extract_video_info.cache_info()
        self.assertEqual(cache_info.hits, 1)
        self.assertEqual(cache_info.misses, 1)

    @patch('yt_dlp.YoutubeDL')
    def test_info_endpoint_error_handling(self, mock_ydl_cls):
        mock_ydl_instance = MagicMock()
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl_instance
        mock_ydl_instance.extract_info.side_effect = Exception('Extraction failed')

        res = self.client.post('/info', json={'url': 'https://example.com/bad_video'})
        self.assertEqual(res.status_code, 500)
        self.assertIn('Extraction failed', res.get_json()['error'])


if __name__ == '__main__':
    unittest.main()
