import pytest
import unittest.mock as mock
from app import app, _get_video_info_cached

@pytest.fixture(autouse=True)
def clear_cache():
    _get_video_info_cached.cache_clear()
    yield

def test_health():
    client = app.test_client()
    res = client.get('/health')
    assert res.status_code == 200
    assert res.json == {'status': 'ok'}

def test_info_missing_url():
    client = app.test_client()
    res = client.post('/info', json={})
    assert res.status_code == 400
    assert res.json == {'error': 'URL required'}

@mock.patch('app.yt_dlp.YoutubeDL')
def test_info_success_and_caching(mock_ydl_cls):
    mock_ydl_instance = mock.MagicMock()
    mock_ydl_cls.return_value.__enter__.return_value = mock_ydl_instance
    mock_ydl_instance.extract_info.return_value = {
        'title': 'Test Video',
        'duration': 120,
        'uploader': 'Test Channel',
        'thumbnail': 'http://example.com/thumb.jpg'
    }

    client = app.test_client()
    res1 = client.post('/info', json={'url': 'https://youtube.com/watch?v=test1234'})
    assert res1.status_code == 200
    assert res1.json == {
        'title': 'Test Video',
        'duration': 120,
        'channel': 'Test Channel',
        'thumbnail': 'http://example.com/thumb.jpg'
    }
    assert mock_ydl_instance.extract_info.call_count == 1

    # Second request to same URL should hit LRU cache and NOT invoke yt_dlp extract_info again
    res2 = client.post('/info', json={'url': 'https://youtube.com/watch?v=test1234'})
    assert res2.status_code == 200
    assert res2.json == res1.json
    assert mock_ydl_instance.extract_info.call_count == 1
