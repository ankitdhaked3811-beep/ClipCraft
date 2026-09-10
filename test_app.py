import pytest
from unittest.mock import patch
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

def test_get_info_no_url(client):
    response = client.post('/info', json={})
    assert response.status_code == 400
    assert 'error' in response.get_json()

@patch('yt_dlp.YoutubeDL')
def test_get_info_success_and_caching(mock_ydl_class, client):
    # Clear lru cache before test
    _fetch_video_info.cache_clear()

    mock_ydl_instance = mock_ydl_class.return_value.__enter__.return_value
    mock_ydl_instance.extract_info.return_value = {
        'title': 'Test Video',
        'duration': 120,
        'uploader': 'Test Channel',
        'thumbnail': 'http://example.com/thumb.jpg'
    }

    test_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'

    # First call: should trigger YoutubeDL call
    response1 = client.post('/info', json={'url': test_url})
    assert response1.status_code == 200
    data1 = response1.get_json()
    assert data1['title'] == 'Test Video'
    assert mock_ydl_instance.extract_info.call_count == 1

    # Second call with same URL: should hit lru_cache without calling YoutubeDL again
    response2 = client.post('/info', json={'url': test_url})
    assert response2.status_code == 200
    data2 = response2.get_json()
    assert data2['title'] == 'Test Video'
    assert mock_ydl_instance.extract_info.call_count == 1  # count remains 1 due to cache!
