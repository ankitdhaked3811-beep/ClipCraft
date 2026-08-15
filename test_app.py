from unittest.mock import patch
import pytest
import app as app_module
from app import app, _get_video_info

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

@patch('app._get_video_info')
def test_info_endpoint_success(mock_get_info, client):
    mock_get_info.return_value = {
        'title': 'Test Video',
        'duration': 120,
        'channel': 'Test Channel',
        'thumbnail': 'http://example.com/thumb.jpg'
    }

    response = client.post('/info', json={'url': 'https://www.youtube.com/watch?v=mock123'})
    assert response.status_code == 200
    assert response.get_json() == {
        'title': 'Test Video',
        'duration': 120,
        'channel': 'Test Channel',
        'thumbnail': 'http://example.com/thumb.jpg'
    }
    mock_get_info.assert_called_once_with('https://www.youtube.com/watch?v=mock123')

def test_info_caching():
    _get_video_info.cache_clear()
    fake_url = 'https://www.youtube.com/watch?v=cache_test_unique'
    mock_info = {
        'title': 'Cached Video',
        'duration': 60,
        'uploader': 'Cache Channel',
        'thumbnail': 'http://example.com/cached.jpg'
    }

    with patch.object(app_module.yt_dlp.YoutubeDL, 'extract_info', return_value=mock_info) as mock_extract:
        res1 = _get_video_info(fake_url)
        res2 = _get_video_info(fake_url)

        assert res1 == res2
        assert mock_extract.call_count == 1
        assert res1['title'] == 'Cached Video'

def test_clip_endpoint_missing_url(client):
    response = client.post('/clip', json={})
    assert response.status_code == 400
    assert response.get_json() == {'error': 'URL required'}

def test_clip_endpoint_exceeds_max_duration(client):
    response = client.post('/clip', json={'url': 'https://www.youtube.com/watch?v=test', 'start': 0, 'end': 200})
    assert response.status_code == 400
    assert response.get_json() == {'error': 'Max 3 minutes allowed'}
