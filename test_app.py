import pytest
from unittest.mock import patch, MagicMock
from app import app, _extract_video_info

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
def test_info_caching_performance(mock_ydl_class, client):
    # Reset cache before test
    _extract_video_info.cache_clear()

    mock_ydl = MagicMock()
    mock_ydl_class.return_value.__enter__.return_value = mock_ydl
    mock_ydl.extract_info.return_value = {
        'title': 'Test Video',
        'duration': 120,
        'uploader': 'Test Channel',
        'thumbnail': 'https://example.com/thumb.jpg'
    }

    test_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'

    # First request - cache miss
    res1 = client.post('/info', json={'url': test_url})
    assert res1.status_code == 200
    assert res1.get_json()['title'] == 'Test Video'
    assert mock_ydl.extract_info.call_count == 1

    # Second request - cache hit!
    res2 = client.post('/info', json={'url': test_url})
    assert res2.status_code == 200
    assert res2.get_json()['title'] == 'Test Video'
    # YoutubeDL extract_info should NOT have been called again
    assert mock_ydl.extract_info.call_count == 1

    # Check LRU cache stats
    cache_info = _extract_video_info.cache_info()
    assert cache_info.hits == 1
    assert cache_info.misses == 1

def test_clip_validation(client):
    # Missing URL
    res1 = client.post('/clip', json={'start': 0, 'end': 10})
    assert res1.status_code == 400

    # Exceeding duration limit (>185s)
    res2 = client.post('/clip', json={'url': 'https://example.com/video', 'start': 0, 'end': 200})
    assert res2.status_code == 400
    assert 'Max 3 minutes allowed' in res2.get_json()['error']
