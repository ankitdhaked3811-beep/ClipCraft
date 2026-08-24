import pytest
from unittest.mock import patch, MagicMock
from app import app, temp_files, _info_cache

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
def test_info_success_and_caching(mock_ydl_cls, client):
    _info_cache.clear()
    mock_ydl = MagicMock()
    mock_ydl_cls.return_value.__enter__.return_value = mock_ydl
    mock_ydl.extract_info.return_value = {
        'title': 'Test Video',
        'duration': 120,
        'uploader': 'Test Channel',
        'thumbnail': 'https://example.com/thumb.jpg'
    }

    url = 'https://youtube.com/watch?v=cachetest123'

    # First request - should call yt_dlp
    response1 = client.post('/info', json={'url': url})
    assert response1.status_code == 200
    assert response1.json == {
        'title': 'Test Video',
        'duration': 120,
        'channel': 'Test Channel',
        'thumbnail': 'https://example.com/thumb.jpg'
    }
    assert mock_ydl.extract_info.call_count == 1

    # Second request with same URL - should hit cache and NOT call yt_dlp again
    response2 = client.post('/info', json={'url': url})
    assert response2.status_code == 200
    assert response2.json == response1.json
    assert mock_ydl.extract_info.call_count == 1

def test_clip_missing_url(client):
    response = client.post('/clip', json={})
    assert response.status_code == 400
    assert response.json == {'error': 'URL required'}

def test_clip_exceeds_max_duration(client):
    response = client.post('/clip', json={'url': 'https://youtube.com/watch?v=test12345', 'start': 0, 'end': 200})
    assert response.status_code == 400
    assert response.json == {'error': 'Max 3 minutes allowed'}
