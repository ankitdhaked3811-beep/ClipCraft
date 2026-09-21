import pytest
from unittest.mock import patch, MagicMock
from app import app, _get_cached_video_info

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_endpoint(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.get_json() == {'status': 'ok'}

def test_info_endpoint_missing_url(client):
    response = client.post('/info', json={})
    assert response.status_code == 400
    assert 'error' in response.get_json()

@patch('yt_dlp.YoutubeDL')
def test_info_endpoint_caching(mock_ydl, client):
    _get_cached_video_info.cache_clear()

    mock_instance = MagicMock()
    mock_ydl.return_value.__enter__.return_value = mock_instance
    mock_instance.extract_info.return_value = {
        'title': 'Test Video',
        'duration': 120,
        'uploader': 'Test Channel',
        'thumbnail': 'http://example.com/thumb.jpg'
    }

    test_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'

    # First call - cache miss
    resp1 = client.post('/info', json={'url': test_url})
    assert resp1.status_code == 200
    data1 = resp1.get_json()
    assert data1['title'] == 'Test Video'
    assert data1['duration'] == 120
    assert data1['channel'] == 'Test Channel'
    assert data1['thumbnail'] == 'http://example.com/thumb.jpg'

    assert mock_instance.extract_info.call_count == 1

    # Second call - should hit cache and NOT call yt_dlp again
    resp2 = client.post('/info', json={'url': test_url})
    assert resp2.status_code == 200
    data2 = resp2.get_json()
    assert data2 == data1

    # Extract info should STILL have been called only once!
    assert mock_instance.extract_info.call_count == 1
