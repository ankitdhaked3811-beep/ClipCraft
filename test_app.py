import time
from unittest.mock import patch
from app import app, fetch_info_cached

def test_health():
    client = app.test_client()
    response = client.get('/health')
    assert response.status_code == 200
    assert response.get_json() == {'status': 'ok'}

def test_get_info_missing_url():
    client = app.test_client()
    response = client.post('/info', json={})
    assert response.status_code == 400
    assert 'error' in response.get_json()

@patch('yt_dlp.YoutubeDL')
def test_get_info_cached_success(mock_yt_dlp):
    fetch_info_cached.cache_clear()

    mock_instance = mock_yt_dlp.return_value.__enter__.return_value
    mock_instance.extract_info.return_value = {
        'title': 'Test Video',
        'duration': 120,
        'uploader': 'Test Channel',
        'thumbnail': 'https://example.com/thumb.jpg',
    }

    client = app.test_client()

    # First request - should call yt-dlp
    resp1 = client.post('/info', json={'url': 'https://www.youtube.com/watch?v=mock123'})
    assert resp1.status_code == 200
    data1 = resp1.get_json()
    assert data1['title'] == 'Test Video'
    assert data1['duration'] == 120
    assert data1['channel'] == 'Test Channel'

    initial_call_count = mock_instance.extract_info.call_count
    assert initial_call_count > 0

    # Second request with same URL - should hit cache and NOT call yt-dlp again
    resp2 = client.post('/info', json={'url': 'https://www.youtube.com/watch?v=mock123'})
    assert resp2.status_code == 200
    assert resp2.get_json() == data1
    assert mock_instance.extract_info.call_count == initial_call_count

def test_create_clip_validation():
    client = app.test_client()

    # Missing URL
    resp_missing = client.post('/clip', json={})
    assert resp_missing.status_code == 400
    assert resp_missing.get_json()['error'] == 'URL required'

    # Duration too long (> 185s)
    resp_long = client.post('/clip', json={'url': 'https://example.com', 'start': 0, 'end': 200})
    assert resp_long.status_code == 400
    assert resp_long.get_json()['error'] == 'Max 3 minutes allowed'
