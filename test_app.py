import time
import pytest
from unittest.mock import patch, MagicMock
from app import app, INFO_CACHE, CACHE_TTL_SECONDS, get_cached_info, set_cached_info

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        INFO_CACHE.clear()
        yield client
        INFO_CACHE.clear()

def test_health_endpoint(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json == {'status': 'ok'}

def test_info_missing_url(client):
    response = client.post('/info', json={})
    assert response.status_code == 400
    assert 'error' in response.json

def test_info_caching_performance(client):
    test_url = 'https://www.youtube.com/watch?v=mock_video_id'
    mock_info = {
        'title': 'Test Video Title',
        'duration': 120,
        'uploader': 'Test Channel',
        'thumbnail': 'https://example.com/thumb.jpg',
    }

    with patch('yt_dlp.YoutubeDL') as mock_ydl_cls:
        mock_ydl_instance = MagicMock()
        mock_ydl_instance.extract_info.return_value = mock_info
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl_instance

        # First request - should call yt_dlp
        t0 = time.time()
        res1 = client.post('/info', json={'url': test_url})
        t1 = time.time()
        dur1 = t1 - t0

        assert res1.status_code == 200
        assert res1.json['title'] == 'Test Video Title'
        assert mock_ydl_instance.extract_info.call_count == 1

        # Second request - served from cache
        t2 = time.time()
        res2 = client.post('/info', json={'url': test_url})
        t3 = time.time()
        dur2 = t3 - t2

        assert res2.status_code == 200
        assert res2.json['title'] == 'Test Video Title'

        # yt_dlp should NOT have been called a second time
        assert mock_ydl_instance.extract_info.call_count == 1

        # Cached call should be faster
        assert dur2 <= dur1 or dur2 < 0.005

def test_cache_ttl_expiration(client):
    test_url = 'https://www.youtube.com/watch?v=expired_video'
    set_cached_info(test_url, {'title': 'Old Title'})

    # Artificially age the entry past TTL
    timestamp, val = INFO_CACHE[test_url]
    INFO_CACHE[test_url] = (timestamp - CACHE_TTL_SECONDS - 10, val)

    assert get_cached_info(test_url) is None

def test_clip_missing_url(client):
    response = client.post('/clip', json={})
    assert response.status_code == 400
    assert 'error' in response.json

def test_clip_exceeds_max_duration(client):
    response = client.post('/clip', json={
        'url': 'https://www.youtube.com/watch?v=test',
        'start': 0,
        'end': 200
    })
    assert response.status_code == 400
    assert 'Max 3 minutes allowed' in response.json['error']
