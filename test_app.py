from unittest.mock import patch
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

def test_info_endpoint_missing_url(client):
    response = client.post('/info', json={})
    assert response.status_code == 400
    assert response.get_json() == {'error': 'URL required'}

@patch('yt_dlp.YoutubeDL')
def test_info_endpoint_and_caching(mock_yt_dlp_class, client):
    # Clear cache before test
    fetch_video_info.cache_clear()

    # Setup mock
    mock_ydl_instance = mock_yt_dlp_class.return_value.__enter__.return_value
    mock_ydl_instance.extract_info.return_value = {
        'title': 'Sample Video Title',
        'duration': 180,
        'uploader': 'Test Channel',
        'thumbnail': 'https://example.com/thumb.jpg',
    }

    url = 'https://www.youtube.com/watch?v=mock123'

    # First request - cache miss
    response1 = client.post('/info', json={'url': url})
    assert response1.status_code == 200
    data1 = response1.get_json()
    assert data1['title'] == 'Sample Video Title'
    assert data1['duration'] == 180
    assert mock_ydl_instance.extract_info.call_count == 1

    # Second request - cache hit
    response2 = client.post('/info', json={'url': url})
    assert response2.status_code == 200
    data2 = response2.get_json()
    assert data2 == data1
    # Check extract_info was NOT called again because result came from lru_cache
    assert mock_ydl_instance.extract_info.call_count == 1
