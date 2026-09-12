import pytest
from app import app
import os
import json
from unittest.mock import patch

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health(client):
    rv = client.get('/health')
    assert rv.status_code == 200
    assert rv.get_json() == {'status': 'ok'}

def test_get_info_no_url(client):
    rv = client.post('/info', json={})
    assert rv.status_code == 400
    assert 'error' in rv.get_json()

@patch('yt_dlp.YoutubeDL')
def test_get_info_success(mock_ydl, client):
    mock_instance = mock_ydl.return_value.__enter__.return_value
    mock_instance.extract_info.return_value = {
        'title': 'Test Video',
        'duration': 100,
        'uploader': 'Test Channel',
        'thumbnail': 'https://example.com/thumb.jpg'
    }
    rv = client.post('/info', json={'url': 'https://youtube.com/watch?v=123'})
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['title'] == 'Test Video'
    assert data['duration'] == 100

def test_create_clip_no_url(client):
    rv = client.post('/clip', json={})
    assert rv.status_code == 400

def test_create_clip_too_long(client):
    rv = client.post('/clip', json={'url': 'https://youtube.com/watch?v=123', 'start': 0, 'end': 200})
    assert rv.status_code == 400

@patch('yt_dlp.YoutubeDL')
def test_create_clip_success_and_cleanup(mock_ydl):
    tmpdir_created = []

    def dummy_download(urls):
        outtmpl = mock_ydl.call_args[0][0]['outtmpl']
        tmpdir = os.path.dirname(outtmpl)
        tmpdir_created.append(tmpdir)
        with open(outtmpl, 'wb') as f:
            f.write(b'dummy video content')

    mock_instance = mock_ydl.return_value.__enter__.return_value
    mock_instance.download.side_effect = dummy_download

    app.config['TESTING'] = True
    with app.test_request_context('/clip', method='POST', json={'url': 'https://youtube.com/watch?v=123', 'start': 0, 'end': 10, 'format_type': 'video'}):
        res = app.full_dispatch_request()
        assert res.status_code == 200
        assert len(tmpdir_created) == 1
        tmpdir = tmpdir_created[0]
        assert os.path.exists(tmpdir)

        # Consuming WSGI iterator and closing response triggers call_on_close
        _ = list(res.response)
        res.close()
        assert not os.path.exists(tmpdir)
