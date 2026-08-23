import pytest
from unittest.mock import patch
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

def test_get_info_missing_url(client):
    response = client.post('/info', json={})
    assert response.status_code == 400
    assert response.get_json() == {'error': 'URL required'}

def test_get_info_caching(client):
    _extract_video_info.cache_clear()
    fake_info = {
        'title': 'Test Title',
        'duration': 120,
        'uploader': 'Test Channel',
        'thumbnail': 'http://example.com/thumb.jpg',
    }

    with patch('yt_dlp.YoutubeDL') as mock_ydl_cls:
        mock_ydl_instance = mock_ydl_cls.return_value.__enter__.return_value
        mock_ydl_instance.extract_info.return_value = fake_info

        # First call
        res1 = client.post('/info', json={'url': 'https://youtube.com/watch?v=test1234'})
        assert res1.status_code == 200
        assert res1.get_json() == {
            'title': 'Test Title',
            'duration': 120,
            'channel': 'Test Channel',
            'thumbnail': 'http://example.com/thumb.jpg',
        }
        assert mock_ydl_instance.extract_info.call_count == 1

        # Second call (should hit lru_cache)
        res2 = client.post('/info', json={'url': 'https://youtube.com/watch?v=test1234'})
        assert res2.status_code == 200
        assert res2.get_json() == res1.get_json()
        assert mock_ydl_instance.extract_info.call_count == 1  # Not incremented due to cache hit

def test_create_clip_missing_url(client):
    response = client.post('/clip', json={})
    assert response.status_code == 400
    assert response.get_json() == {'error': 'URL required'}

def test_create_clip_duration_limit(client):
    response = client.post('/clip', json={
        'url': 'https://youtube.com/watch?v=test1234',
        'start': 0,
        'end': 200
    })
    assert response.status_code == 400
    assert response.get_json() == {'error': 'Max 3 minutes allowed'}
