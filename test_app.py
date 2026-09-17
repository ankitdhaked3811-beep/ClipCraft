import pytest
from unittest.mock import patch, MagicMock
import os
import tempfile
import time
from app import app, _get_cached_info, cleanup_file

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_endpoint(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.get_json() == {'status': 'ok'}

def test_info_missing_url(client):
    response = client.post('/info', json={})
    assert response.status_code == 400
    assert response.get_json() == {'error': 'URL required'}

def test_info_cached_metadata(client):
    _get_cached_info.cache_clear()

    mock_info = {
        'title': 'Test Video Title',
        'duration': 120,
        'uploader': 'Test Channel',
        'thumbnail': 'https://example.com/thumb.jpg'
    }

    with patch('yt_dlp.YoutubeDL') as mock_ydl_cls:
        mock_ydl = MagicMock()
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = mock_info

        url = 'https://www.youtube.com/watch?v=test_cache'

        # First request (cache miss)
        res1 = client.post('/info', json={'url': url})
        assert res1.status_code == 200
        data1 = res1.get_json()
        assert data1['title'] == 'Test Video Title'
        assert data1['duration'] == 120
        assert data1['channel'] == 'Test Channel'

        # Second request (cache hit)
        res2 = client.post('/info', json={'url': url})
        assert res2.status_code == 200
        data2 = res2.get_json()
        assert data2 == data1

        # Verify yt_dlp extract_info was called only ONCE due to caching
        assert mock_ydl.extract_info.call_count == 1

def test_clip_missing_url(client):
    response = client.post('/clip', json={})
    assert response.status_code == 400
    assert response.get_json() == {'error': 'URL required'}

def test_clip_exceeds_max_duration(client):
    response = client.post('/clip', json={
        'url': 'https://example.com/video',
        'start': 0,
        'end': 200
    })
    assert response.status_code == 400
    assert response.get_json() == {'error': 'Max 3 minutes allowed'}

def test_cleanup_file_removes_temp_subfolder():
    tmpdir = tempfile.mkdtemp()
    out_file = os.path.join(tmpdir, 'clip.mp4')
    with open(out_file, 'w') as f:
        f.write('dummy clip content')

    assert os.path.exists(out_file)
    assert os.path.exists(tmpdir)

    cleanup_file(out_file, delay=0.01)
    time.sleep(0.05)

    # Confirm temp subfolder was completely removed
    assert not os.path.exists(tmpdir)

def test_cleanup_file_does_not_remove_system_temp():
    sys_temp = tempfile.gettempdir()
    file_in_sys_temp = os.path.join(sys_temp, 'test_standalone_file.txt')
    with open(file_in_sys_temp, 'w') as f:
        f.write('test file directly in system temp')

    cleanup_file(file_in_sys_temp, delay=0.01)
    time.sleep(0.05)

    # Confirm system temp dir was NOT removed, but individual file was removed
    assert os.path.exists(sys_temp)
    assert not os.path.exists(file_in_sys_temp)
