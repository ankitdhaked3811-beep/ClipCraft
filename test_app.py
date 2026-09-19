import pytest
from unittest.mock import patch, MagicMock
from app import app, fetch_video_info, temp_files

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_endpoint(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.get_json() == {'status': 'ok'}

def test_info_missing_url(client):
    response = client.post('/info', json={})
    assert response.status_code == 400
    assert response.get_json() == {'error': 'URL required'}

@patch('yt_dlp.YoutubeDL')
def test_info_cached(mock_yt_dlp, client):
    # Clear cache before test
    fetch_video_info.cache_clear()

    mock_instance = MagicMock()
    mock_instance.extract_info.return_value = {
        'title': 'Test Video',
        'duration': 120,
        'uploader': 'Test Channel',
        'thumbnail': 'http://example.com/thumb.jpg'
    }
    mock_yt_dlp.return_value.__enter__.return_value = mock_instance

    # First call - should call yt_dlp
    resp1 = client.post('/info', json={'url': 'https://youtube.com/watch?v=123'})
    assert resp1.status_code == 200
    assert resp1.get_json()['title'] == 'Test Video'
    assert mock_instance.extract_info.call_count == 1

    # Second call with same URL - should use cache and not call yt_dlp again
    resp2 = client.post('/info', json={'url': 'https://youtube.com/watch?v=123'})
    assert resp2.status_code == 200
    assert resp2.get_json()['title'] == 'Test Video'
    assert mock_instance.extract_info.call_count == 1  # Still 1 because cached!

def test_clip_missing_url(client):
    response = client.post('/clip', json={})
    assert response.status_code == 400
    assert response.get_json() == {'error': 'URL required'}

def test_clip_duration_too_long(client):
    response = client.post('/clip', json={'url': 'https://youtube.com/watch?v=123', 'start': 0, 'end': 200})
    assert response.status_code == 400
    assert response.get_json() == {'error': 'Max 3 minutes allowed'}
