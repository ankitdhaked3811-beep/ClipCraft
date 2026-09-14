import pytest
from unittest.mock import patch
import app as app_module

@pytest.fixture
def client():
    app_module.app.config['TESTING'] = True
    with app_module.app.test_client() as client:
        yield client

def test_health(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.get_json() == {'status': 'ok'}

def test_info_missing_url(client):
    response = client.post('/info', json={})
    assert response.status_code == 400
    assert 'error' in response.get_json()

@patch('app.yt_dlp.YoutubeDL')
def test_info_caching(mock_ydl_cls, client):
    mock_ydl_instance = mock_ydl_cls.return_value.__enter__.return_value
    mock_ydl_instance.extract_info.return_value = {
        'title': 'Test Video',
        'duration': 120,
        'uploader': 'Test Channel',
        'thumbnail': 'http://example.com/thumb.jpg',
    }

    url = 'http://example.com/watch?v=123'

    # Clear cache before test
    app_module.fetch_video_info.cache_clear()

    # First request
    res1 = client.post('/info', json={'url': url})
    assert res1.status_code == 200
    json1 = res1.get_json()
    assert json1['title'] == 'Test Video'
    assert json1['duration'] == 120
    assert json1['channel'] == 'Test Channel'
    assert json1['thumbnail'] == 'http://example.com/thumb.jpg'
    assert mock_ydl_instance.extract_info.call_count == 1

    # Second request with same URL - should be served from cache
    res2 = client.post('/info', json={'url': url})
    assert res2.status_code == 200
    json2 = res2.get_json()
    assert json2 == json1
    # extract_info should still have been called only once
    assert mock_ydl_instance.extract_info.call_count == 1

def test_clip_validation(client):
    # Missing URL
    res = client.post('/clip', json={})
    assert res.status_code == 400

    # Clip duration > 185s
    res2 = client.post('/clip', json={'url': 'http://example.com/v', 'start': 0, 'end': 200})
    assert res2.status_code == 400
    assert res2.get_json()['error'] == 'Max 3 minutes allowed'
