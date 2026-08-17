import pytest
from unittest.mock import patch
from app import app, _get_cached_video_info

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json == {'status': 'ok'}

def test_info_missing_url(client):
    response = client.post('/info', json={})
    assert response.status_code == 400
    assert 'error' in response.json

@patch('app.yt_dlp.YoutubeDL')
def test_info_caching(mock_yt_dlp, client):
    # Clear cache before test
    _get_cached_video_info.cache_clear()

    mock_instance = mock_yt_dlp.return_value.__enter__.return_value
    mock_instance.extract_info.return_value = {
        'title': 'Test Title',
        'duration': 120,
        'uploader': 'Test Channel',
        'thumbnail': 'https://example.com/thumb.jpg',
    }

    test_url = 'https://www.youtube.com/watch?v=test12345'

    # First request - should call yt_dlp
    resp1 = client.post('/info', json={'url': test_url})
    assert resp1.status_code == 200
    assert resp1.json == {
        'title': 'Test Title',
        'duration': 120,
        'channel': 'Test Channel',
        'thumbnail': 'https://example.com/thumb.jpg',
    }
    assert mock_instance.extract_info.call_count == 1

    # Second request with same URL - should use cache and not call yt_dlp again
    resp2 = client.post('/info', json={'url': test_url})
    assert resp2.status_code == 200
    assert resp2.json == resp1.json
    assert mock_instance.extract_info.call_count == 1
