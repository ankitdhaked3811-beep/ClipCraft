import pytest
from unittest.mock import patch, MagicMock
from app import app, INFO_CACHE, CACHE_LOCK

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with CACHE_LOCK:
        INFO_CACHE.clear()
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
def test_info_endpoint_caching_and_noplaylist(mock_ydl_cls, client):
    mock_ydl_instance = MagicMock()
    mock_ydl_cls.return_value.__enter__.return_value = mock_ydl_instance
    mock_ydl_instance.extract_info.return_value = {
        'title': 'Test Video',
        'duration': 120,
        'uploader': 'Test Channel',
        'thumbnail': 'https://example.com/thumb.jpg',
    }

    test_url = 'https://www.youtube.com/watch?v=test12345'

    # First request: should invoke extract_info
    response1 = client.post('/info', json={'url': test_url})
    assert response1.status_code == 200
    data1 = response1.get_json()
    assert data1['title'] == 'Test Video'
    assert data1['duration'] == 120
    assert data1['channel'] == 'Test Channel'
    assert data1['thumbnail'] == 'https://example.com/thumb.jpg'

    # Verify YoutubeDL options had noplaylist set to True
    opts = mock_ydl_cls.call_args[0][0]
    assert opts.get('noplaylist') is True

    assert mock_ydl_instance.extract_info.call_count == 1

    # Second request with same URL: should hit cache and NOT invoke extract_info again
    response2 = client.post('/info', json={'url': test_url})
    assert response2.status_code == 200
    data2 = response2.get_json()
    assert data2 == data1
    assert mock_ydl_instance.extract_info.call_count == 1  # Still 1! Fast path hit!

def test_clip_endpoint_validation(client):
    # Missing URL
    response = client.post('/clip', json={})
    assert response.status_code == 400

    # Duration > 185s
    response = client.post('/clip', json={'url': 'https://example.com', 'start': 0, 'end': 200})
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Max 3 minutes allowed'
