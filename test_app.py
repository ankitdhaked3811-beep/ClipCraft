from unittest.mock import patch, MagicMock
import pytest
from app import app, fetch_video_info

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_endpoint(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.get_json() == {'status': 'ok'}

def test_get_info_missing_url(client):
    response = client.post('/info', json={})
    assert response.status_code == 400
    assert response.get_json() == {'error': 'URL required'}

@patch('app.yt_dlp.YoutubeDL')
def test_get_info_success_and_caching(mock_ydl, client):
    mock_instance = MagicMock()
    mock_ydl.return_value.__enter__.return_value = mock_instance
    mock_instance.extract_info.return_value = {
        'title': 'Test Video',
        'duration': 120,
        'uploader': 'Test Channel',
        'thumbnail': 'https://example.com/thumb.jpg'
    }

    test_url = 'https://www.youtube.com/watch?v=test_caching_123'

    # Clear cache before test
    fetch_video_info.cache_clear()

    # First request - should call yt_dlp
    resp1 = client.post('/info', json={'url': test_url})
    assert resp1.status_code == 200
    data1 = resp1.get_json()
    assert data1['title'] == 'Test Video'
    assert data1['duration'] == 120
    assert data1['channel'] == 'Test Channel'
    assert data1['thumbnail'] == 'https://example.com/thumb.jpg'

    # Second request with same URL - should hit LRU cache without invoking yt_dlp again
    resp2 = client.post('/info', json={'url': test_url})
    assert resp2.status_code == 200
    assert resp2.get_json() == data1

    # Verify YoutubeDL was only called once due to LRU caching
    assert mock_instance.extract_info.call_count == 1

def test_clip_missing_url(client):
    response = client.post('/clip', json={})
    assert response.status_code == 400
    assert response.get_json() == {'error': 'URL required'}

def test_clip_exceeds_max_duration(client):
    response = client.post('/clip', json={'url': 'https://example.com/video', 'start': 0, 'end': 200})
    assert response.status_code == 400
    assert response.get_json() == {'error': 'Max 3 minutes allowed'}
