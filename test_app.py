import pytest
from unittest.mock import patch
from app import app, fetch_video_info

@pytest.fixture
def client():
    app.config['TESTING'] = True
    # Clear lru cache before tests
    fetch_video_info.cache_clear()
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
def test_info_caching(mock_ydl_class, client):
    mock_ydl = mock_ydl_class.return_value.__enter__.return_value
    mock_ydl.extract_info.return_value = {
        'title': 'Test Video Title',
        'duration': 120,
        'uploader': 'Test Channel',
        'thumbnail': 'https://example.com/thumb.jpg',
    }

    test_url = 'https://www.youtube.com/watch?v=test12345'

    # First request - should call yt_dlp
    res1 = client.post('/info', json={'url': test_url})
    assert res1.status_code == 200
    assert res1.json['title'] == 'Test Video Title'
    assert res1.json['duration'] == 120
    assert res1.json['channel'] == 'Test Channel'
    assert res1.json['thumbnail'] == 'https://example.com/thumb.jpg'
    assert mock_ydl.extract_info.call_count == 1

    # Second request with same URL - should hit LRU cache and NOT call yt_dlp again
    res2 = client.post('/info', json={'url': test_url})
    assert res2.status_code == 200
    assert res2.json['title'] == 'Test Video Title'
    assert mock_ydl.extract_info.call_count == 1

def test_clip_missing_url(client):
    response = client.post('/clip', json={})
    assert response.status_code == 400
    assert response.json == {'error': 'URL required'}

def test_clip_exceeds_max_duration(client):
    response = client.post('/clip', json={'url': 'http://example.com', 'start': 0, 'end': 200})
    assert response.status_code == 400
    assert response.json == {'error': 'Max 3 minutes allowed'}
