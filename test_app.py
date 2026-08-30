import pytest
from unittest.mock import patch
import app

@pytest.fixture
def client():
    app.app.config['TESTING'] = True
    with app.app.test_client() as client:
        yield client

def test_health(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json == {'status': 'ok'}

def test_info_missing_url(client):
    response = client.post('/info', json={})
    assert response.status_code == 400
    assert response.json == {'error': 'URL required'}

def test_info_caching(client):
    mock_meta = {
        'title': 'Test Video',
        'duration': 120,
        'uploader': 'Test Channel',
        'thumbnail': 'https://example.com/thumb.jpg',
    }

    test_url = 'https://www.w3schools.com/html/mov_bbb.mp4'

    app.fetch_video_info.cache_clear()
    with patch('yt_dlp.YoutubeDL') as MockYoutubeDL:
        mock_ydl_instance = MockYoutubeDL.return_value.__enter__.return_value
        mock_ydl_instance.extract_info.return_value = mock_meta

        # First request should trigger extract_info
        res1 = client.post('/info', json={'url': test_url})
        assert res1.status_code == 200
        assert res1.json['title'] == 'Test Video'
        assert mock_ydl_instance.extract_info.call_count == 1

        # Second request with same URL should hit LRU cache and NOT trigger extract_info again
        res2 = client.post('/info', json={'url': test_url})
        assert res2.status_code == 200
        assert res2.json['title'] == 'Test Video'
        assert mock_ydl_instance.extract_info.call_count == 1
