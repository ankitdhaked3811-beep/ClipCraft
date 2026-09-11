import pytest
from unittest.mock import patch, MagicMock
from app import app, _extract_info_cached

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json == {'status': 'ok'}

def test_get_info_missing_url(client):
    response = client.post('/info', json={})
    assert response.status_code == 400
    assert 'error' in response.json

def test_get_info_success_and_caching(client):
    # Clear cache before test
    _extract_info_cached.cache_clear()

    mock_info = {
        'title': 'Test Video',
        'duration': 120,
        'uploader': 'Test Channel',
        'thumbnail': 'https://example.com/thumb.jpg'
    }

    with patch('yt_dlp.YoutubeDL') as MockYoutubeDL:
        mock_instance = MagicMock()
        mock_instance.extract_info.return_value = mock_info
        MockYoutubeDL.return_value.__enter__.return_value = mock_instance

        test_url = 'https://www.youtube.com/watch?v=mock_video_id'

        # First request should call extract_info
        res1 = client.post('/info', json={'url': test_url})
        assert res1.status_code == 200
        assert res1.json['title'] == 'Test Video'
        assert mock_instance.extract_info.call_count == 1

        # Second request with same URL should hit LRU cache
        res2 = client.post('/info', json={'url': test_url})
        assert res2.status_code == 200
        assert res2.json['title'] == 'Test Video'
        # extract_info should NOT have been called a second time
        assert mock_instance.extract_info.call_count == 1

def test_create_clip_missing_url(client):
    response = client.post('/clip', json={})
    assert response.status_code == 400
    assert response.json == {'error': 'URL required'}

def test_create_clip_exceeds_max_duration(client):
    response = client.post('/clip', json={'url': 'https://example.com', 'start': 0, 'end': 200})
    assert response.status_code == 400
    assert response.json == {'error': 'Max 3 minutes allowed'}
