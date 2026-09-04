from unittest.mock import patch
import pytest
from app import app, get_video_metadata

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
    assert 'error' in response.get_json()

@patch('yt_dlp.YoutubeDL')
def test_info_success_and_cache(mock_yt_dlp_cls, client):
    # Clear cache before test
    get_video_metadata.cache_clear()

    mock_ydl = mock_yt_dlp_cls.return_value.__enter__.return_value
    mock_ydl.extract_info.return_value = {
        'title': 'Test Video',
        'duration': 120,
        'uploader': 'Test Channel',
        'thumbnail': 'https://example.com/thumb.jpg'
    }

    test_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'

    # First call: cache miss, extracts info via yt_dlp
    response1 = client.post('/info', json={'url': test_url})
    assert response1.status_code == 200
    json1 = response1.get_json()
    assert json1['title'] == 'Test Video'
    assert json1['duration'] == 120
    assert mock_ydl.extract_info.call_count == 1

    # Second call with same URL: cache hit, extract_info should not be called again
    response2 = client.post('/info', json={'url': test_url})
    assert response2.status_code == 200
    json2 = response2.get_json()
    assert json2 == json1
    assert mock_ydl.extract_info.call_count == 1  # call_count remains 1 due to @lru_cache

def test_clip_missing_url(client):
    response = client.post('/clip', json={})
    assert response.status_code == 400
    assert 'error' in response.get_json()

def test_clip_duration_exceeded(client):
    response = client.post('/clip', json={'url': 'https://example.com', 'start': 0, 'end': 200})
    assert response.status_code == 400
    assert response.get_json() == {'error': 'Max 3 minutes allowed'}
