import pytest
from unittest.mock import MagicMock, patch
from app import app, _fetch_video_info

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.get_json() == {'status': 'ok'}

def test_info_missing_url(client):
    response = client.post('/info', json={})
    assert response.status_code == 400
    assert response.get_json() == {'error': 'URL required'}

@patch('yt_dlp.YoutubeDL')
def test_info_success_and_caching(mock_ydl_class, client):
    # Clear cache before test
    _fetch_video_info.cache_clear()

    mock_ydl = MagicMock()
    mock_ydl_class.return_value.__enter__.return_value = mock_ydl
    mock_ydl.extract_info.return_value = {
        'title': 'Test Video',
        'duration': 120,
        'uploader': 'Test Channel',
        'thumbnail': 'http://example.com/thumb.jpg',
    }

    test_url = 'https://www.youtube.com/watch?v=test12345'

    # First request - should call yt_dlp
    response1 = client.post('/info', json={'url': test_url})
    assert response1.status_code == 200
    assert response1.get_json() == {
        'title': 'Test Video',
        'duration': 120,
        'channel': 'Test Channel',
        'thumbnail': 'http://example.com/thumb.jpg',
    }
    assert mock_ydl.extract_info.call_count == 1

    # Second request with same URL - should hit LRU cache and NOT call yt_dlp again
    response2 = client.post('/info', json={'url': test_url})
    assert response2.status_code == 200
    assert response2.get_json() == {
        'title': 'Test Video',
        'duration': 120,
        'channel': 'Test Channel',
        'thumbnail': 'http://example.com/thumb.jpg',
    }
    assert mock_ydl.extract_info.call_count == 1

def test_clip_validation(client):
    response = client.post('/clip', json={})
    assert response.status_code == 400
    assert response.get_json() == {'error': 'URL required'}

    response = client.post('/clip', json={'url': 'http://example.com', 'start': 0, 'end': 200})
    assert response.status_code == 400
    assert response.get_json() == {'error': 'Max 3 minutes allowed'}
