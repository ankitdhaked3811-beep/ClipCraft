from unittest.mock import patch
import pytest
from app import app, _extract_info_cached

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

def test_info_success_and_caching(client):
    _extract_info_cached.cache_clear()

    mock_meta = {
        'title': 'Test Video',
        'duration': 120,
        'uploader': 'Test Channel',
        'thumbnail': 'http://example.com/thumb.jpg'
    }

    with patch('yt_dlp.YoutubeDL') as MockYoutubeDL:
        mock_instance = MockYoutubeDL.return_value.__enter__.return_value
        mock_instance.extract_info.return_value = mock_meta

        url = 'https://www.youtube.com/watch?v=test12345'

        # First call: cache miss, invokes extract_info
        res1 = client.post('/info', json={'url': url})
        assert res1.status_code == 200
        data1 = res1.get_json()
        assert data1['title'] == 'Test Video'
        assert data1['duration'] == 120
        assert data1['channel'] == 'Test Channel'
        assert data1['thumbnail'] == 'http://example.com/thumb.jpg'
        assert mock_instance.extract_info.call_count == 1

        # Second call: cache hit, uses cached result without invoking extract_info again
        res2 = client.post('/info', json={'url': url})
        assert res2.status_code == 200
        assert res2.get_json() == data1
        assert mock_instance.extract_info.call_count == 1  # call_count remains 1 due to LRU cache

def test_clip_missing_url(client):
    response = client.post('/clip', json={})
    assert response.status_code == 400
    assert 'error' in response.get_json()

def test_clip_exceeds_max_duration(client):
    response = client.post('/clip', json={'url': 'http://example.com/vid', 'start': 0, 'end': 200})
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Max 3 minutes allowed'
