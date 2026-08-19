import os
import tempfile
import time
from unittest.mock import patch, MagicMock
import pytest

from app import app, temp_files, cleanup_file, _extract_video_info


@pytest.fixture
def client():
    app.config['TESTING'] = True
    _extract_video_info.cache_clear()
    with app.test_client() as client:
        yield client


def test_health_endpoint(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.get_json() == {'status': 'ok'}


def test_info_endpoint_missing_url(client):
    response = client.post('/info', json={})
    assert response.status_code == 400
    assert 'error' in response.get_json()


@patch('yt_dlp.YoutubeDL')
def test_info_endpoint_success_and_caching(mock_yt_dlp, client):
    mock_instance = MagicMock()
    mock_instance.extract_info.return_value = {
        'title': 'Test Video',
        'duration': 120,
        'uploader': 'Test Channel',
        'thumbnail': 'https://example.com/thumb.jpg',
    }
    mock_yt_dlp.return_value.__enter__.return_value = mock_instance

    url = 'https://example.com/watch?v=cached_test'

    # First request - cache miss
    response1 = client.post('/info', json={'url': url})
    assert response1.status_code == 200
    assert mock_yt_dlp.call_count == 1

    # Verify noplaylist is passed to YoutubeDL
    ydl_opts = mock_yt_dlp.call_args[0][0]
    assert ydl_opts.get('noplaylist') is True

    # Second request - cache hit (mock_yt_dlp should NOT be called again)
    response2 = client.post('/info', json={'url': url})
    assert response2.status_code == 200
    assert mock_yt_dlp.call_count == 1  # call count stayed 1 due to LRU cache!
    assert response1.get_json() == response2.get_json()


@patch('yt_dlp.YoutubeDL')
def test_info_endpoint_error(mock_yt_dlp, client):
    mock_instance = MagicMock()
    mock_instance.extract_info.side_effect = Exception('Download error')
    mock_yt_dlp.return_value.__enter__.return_value = mock_instance

    response = client.post('/info', json={'url': 'https://example.com/watch?v=invalid'})
    assert response.status_code == 500
    assert 'error' in response.get_json()


def test_clip_endpoint_missing_url(client):
    response = client.post('/clip', json={})
    assert response.status_code == 400


def test_clip_endpoint_exceeds_max_duration(client):
    response = client.post('/clip', json={'url': 'https://example.com', 'start': 0, 'end': 200})
    assert response.status_code == 400
    assert 'Max 3 minutes allowed' in response.get_json()['error']


@patch('yt_dlp.YoutubeDL')
def test_clip_endpoint_audio_success(mock_yt_dlp, client):
    mock_instance = MagicMock()
    def fake_download(urls):
        opts = mock_yt_dlp.call_args[0][0]
        outtmpl = opts.get('outtmpl', '')
        if '%(ext)s' in outtmpl:
            out_file = outtmpl.replace('%(ext)s', 'mp3')
        else:
            out_file = outtmpl
        os.makedirs(os.path.dirname(out_file), exist_ok=True)
        with open(out_file, 'wb') as f:
            f.write(b'fake audio content')

    mock_instance.download.side_effect = fake_download
    mock_yt_dlp.return_value.__enter__.return_value = mock_instance

    response = client.post('/clip', json={
        'url': 'https://example.com/watch?v=123',
        'start': 0,
        'end': 10,
        'format_type': 'audio',
        'quality': '320kbps'
    })
    assert response.status_code == 200
    assert response.mimetype == 'audio/mpeg'

    # Check noplaylist setting
    opts = mock_yt_dlp.call_args[0][0]
    assert opts.get('noplaylist') is True


def test_cleanup_file_removes_directory():
    tmp_dir = tempfile.mkdtemp()
    file_path = os.path.join(tmp_dir, 'clip.mp4')
    with open(file_path, 'w') as f:
        f.write('test')

    temp_files[file_path] = True
    cleanup_file(file_path, delay=0.01)
    time.sleep(0.05)

    # Directory and file should both be deleted
    assert not os.path.exists(tmp_dir)
    assert not os.path.exists(file_path)
    assert file_path not in temp_files
