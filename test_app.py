from unittest.mock import patch
import pytest
from app import app, fetch_video_info

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
    assert response.json == {'error': 'URL required'}

@patch('yt_dlp.YoutubeDL')
def test_info_success_and_caching(mock_ydl_class, client):
    # Clear cache before test
    fetch_video_info.cache_clear()

    mock_ydl_instance = mock_ydl_class.return_value.__enter__.return_value
    mock_ydl_instance.extract_info.return_value = {
        'title': 'Test Video',
        'duration': 120,
        'uploader': 'Test Channel',
        'thumbnail': 'https://example.com/thumb.jpg'
    }

    url = 'https://www.youtube.com/watch?v=test12345'

    # First call - should call YoutubeDL
    res1 = client.post('/info', json={'url': url})
    assert res1.status_code == 200
    assert res1.json == {
        'title': 'Test Video',
        'duration': 120,
        'channel': 'Test Channel',
        'thumbnail': 'https://example.com/thumb.jpg'
    }
    assert mock_ydl_instance.extract_info.call_count == 1

    # Second call - should hit LRU cache without extra extract_info call
    res2 = client.post('/info', json={'url': url})
    assert res2.status_code == 200
    assert res2.json == res1.json
    assert mock_ydl_instance.extract_info.call_count == 1

def test_clip_missing_url(client):
    response = client.post('/clip', json={})
    assert response.status_code == 400
    assert response.json == {'error': 'URL required'}

def test_clip_exceeds_max_duration(client):
    response = client.post('/clip', json={'url': 'https://example.com', 'start': 0, 'end': 200})
    assert response.status_code == 400
    assert response.json == {'error': 'Max 3 minutes allowed'}
