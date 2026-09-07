import pytest
import time
from unittest.mock import patch, MagicMock
from app import app, info_cache

@pytest.fixture
def client():
    app.config['TESTING'] = True
    info_cache.clear()
    with app.test_client() as client:
        yield client

def test_health_endpoint(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json == {'status': 'ok'}

def test_get_info_missing_url(client):
    response = client.post('/info', json={})
    assert response.status_code == 400
    assert 'error' in response.json

@patch('yt_dlp.YoutubeDL')
def test_get_info_caching(mock_yt_dlp, client):
    mock_instance = MagicMock()
    mock_instance.extract_info.return_value = {
        'title': 'Test Video',
        'duration': 100,
        'uploader': 'Test Channel',
        'thumbnail': 'https://example.com/thumb.jpg'
    }
    mock_yt_dlp.return_value.__enter__.return_value = mock_instance

    url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'

    # First request - should invoke yt_dlp
    resp1 = client.post('/info', json={'url': url})
    assert resp1.status_code == 200
    assert resp1.json['title'] == 'Test Video'
    assert mock_instance.extract_info.call_count == 1

    # Second request with same URL - should hit cache and NOT invoke yt_dlp again
    resp2 = client.post('/info', json={'url': url})
    assert resp2.status_code == 200
    assert resp2.json['title'] == 'Test Video'
    assert mock_instance.extract_info.call_count == 1

def test_create_clip_missing_url(client):
    response = client.post('/clip', json={})
    assert response.status_code == 400
    assert response.json == {'error': 'URL required'}

def test_create_clip_exceeds_max_duration(client):
    response = client.post('/clip', json={'url': 'http://example.com', 'start': 0, 'end': 200})
    assert response.status_code == 400
    assert response.json == {'error': 'Max 3 minutes allowed'}
