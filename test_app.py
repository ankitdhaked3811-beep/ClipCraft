import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json == {'status': 'ok'}

def test_info_missing_url(client):
    response = client.post('/info', json={})
    assert response.status_code == 400
    assert response.json == {'error': 'URL required'}

def test_clip_missing_url(client):
    response = client.post('/clip', json={})
    assert response.status_code == 400
    assert response.json == {'error': 'URL required'}

def test_clip_exceeds_max_duration(client):
    response = client.post('/clip', json={
        'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'start': 0,
        'end': 200
    })
    assert response.status_code == 400
    assert response.json == {'error': 'Max 3 minutes allowed'}
