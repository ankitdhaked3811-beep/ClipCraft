import pytest
from unittest.mock import patch
import app as flask_app

@pytest.fixture
def client():
    flask_app.app.config['TESTING'] = True
    flask_app._extract_info_cached.cache_clear()
    with flask_app.app.test_client() as client:
        yield client

def test_health(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.get_json() == {'status': 'ok'}

def test_get_info_missing_url(client):
    response = client.post('/info', json={})
    assert response.status_code == 400
    assert response.get_json() == {'error': 'URL required'}

def test_get_info(client):
    fake_info = {
        'title': 'Sample Video',
        'duration': 120,
        'uploader': 'Sample Channel',
        'thumbnail': 'https://example.com/thumb.jpg',
    }

    with patch('yt_dlp.YoutubeDL') as mock_ydl:
        mock_instance = mock_ydl.return_value.__enter__.return_value
        mock_instance.extract_info.return_value = fake_info

        response = client.post('/info', json={'url': 'https://example.com/watch?v=123'})
        assert response.status_code == 200
        data = response.get_json()
        assert data['title'] == 'Sample Video'
        assert data['duration'] == 120
        assert data['channel'] == 'Sample Channel'
        assert data['thumbnail'] == 'https://example.com/thumb.jpg'

def test_get_info_cache(client):
    fake_info = {
        'title': 'Cached Video',
        'duration': 60,
        'uploader': 'Cached Channel',
        'thumbnail': 'https://example.com/cached.jpg',
    }

    with patch('yt_dlp.YoutubeDL') as mock_ydl:
        mock_instance = mock_ydl.return_value.__enter__.return_value
        mock_instance.extract_info.return_value = fake_info

        url = 'https://example.com/watch?v=cache_test'

        # First request: should hit yt_dlp
        res1 = client.post('/info', json={'url': url})
        assert res1.status_code == 200
        assert mock_instance.extract_info.call_count == 1

        # Second request: should hit LRU cache, yt_dlp extract_info not called again
        res2 = client.post('/info', json={'url': url})
        assert res2.status_code == 200
        assert mock_instance.extract_info.call_count == 1
        assert res1.get_json() == res2.get_json()
