import pytest
from unittest.mock import patch, MagicMock
from app import app

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

@patch('yt_dlp.YoutubeDL')
def test_info_endpoint_success(mock_ydl_class, client):
    mock_ydl = MagicMock()
    mock_ydl.extract_info.return_value = {
        'title': 'Sample Video Title',
        'duration': 120,
        'uploader': 'Sample Channel',
        'thumbnail': 'https://example.com/thumb.jpg'
    }
    mock_ydl_class.return_value.__enter__.return_value = mock_ydl

    response = client.post('/info', json={'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'})
    assert response.status_code == 200
    data = response.get_json()
    assert data['title'] == 'Sample Video Title'
    assert data['duration'] == 120
    assert data['channel'] == 'Sample Channel'
    assert data['thumbnail'] == 'https://example.com/thumb.jpg'

    # Verify YoutubeDL options included performance optimizations
    mock_ydl_class.assert_called_once()
    ydl_opts = mock_ydl_class.call_args[0][0]
    assert ydl_opts.get('noplaylist') is True
    assert ydl_opts.get('extract_flat') == 'in_playlist'
    assert ydl_opts.get('skip_download') is True

def test_clip_endpoint_missing_url(client):
    response = client.post('/clip', json={})
    assert response.status_code == 400
    assert response.get_json() == {'error': 'URL required'}

def test_clip_endpoint_duration_exceeded(client):
    response = client.post('/clip', json={'url': 'https://youtube.com/watch?v=test', 'start': 0, 'end': 200})
    assert response.status_code == 400
    assert response.get_json() == {'error': 'Max 3 minutes allowed'}
