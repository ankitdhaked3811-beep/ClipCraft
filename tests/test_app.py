import pytest
import json
from unittest.mock import patch
from app import app, fetch_video_info

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health(client):
    rv = client.get('/health')
    assert rv.status_code == 200
    assert rv.get_json() == {'status': 'ok'}

def test_info_missing_url(client):
    rv = client.post('/info', json={})
    assert rv.status_code == 400
    assert 'error' in rv.get_json()

@patch('app.yt_dlp.YoutubeDL.extract_info')
def test_info_success(mock_extract, client):
    mock_extract.return_value = {
        'title': 'Test Video',
        'duration': 120,
        'uploader': 'Test Channel',
        'thumbnail': 'https://example.com/thumb.jpg',
    }
    fetch_video_info.cache_clear()
    test_url = 'https://www.youtube.com/watch?v=mock'
    rv = client.post('/info', json={'url': test_url})
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['title'] == 'Test Video'
    assert data['duration'] == 120
    assert data['channel'] == 'Test Channel'
    assert data['thumbnail'] == 'https://example.com/thumb.jpg'

@patch('app.yt_dlp.YoutubeDL.extract_info')
def test_info_caching(mock_extract, client):
    mock_extract.return_value = {
        'title': 'Test Video',
        'duration': 120,
        'uploader': 'Test Channel',
        'thumbnail': 'https://example.com/thumb.jpg',
    }
    test_url = 'https://www.youtube.com/watch?v=mock_cache'
    fetch_video_info.cache_clear()

    rv1 = client.post('/info', json={'url': test_url})
    assert rv1.status_code == 200
    info1 = fetch_video_info.cache_info()
    assert info1.hits == 0
    assert info1.misses == 1
    assert mock_extract.call_count == 1

    rv2 = client.post('/info', json={'url': test_url})
    assert rv2.status_code == 200
    info2 = fetch_video_info.cache_info()
    assert info2.hits == 1
    assert info2.misses == 1
    assert mock_extract.call_count == 1
