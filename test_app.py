import pytest
from app import app, _fetch_info

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_endpoint(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json == {'status': 'ok'}

def test_info_missing_url(client):
    response = client.post('/info', json={})
    assert response.status_code == 400
    assert 'error' in response.json

def test_info_success_and_cache(client):
    url = 'https://soundcloud.com/forss/flickermood'

    # First request
    res1 = client.post('/info', json={'url': url})
    assert res1.status_code == 200
    data1 = res1.json
    assert 'title' in data1
    assert 'duration' in data1
    assert 'channel' in data1
    assert 'thumbnail' in data1

    # Check cache info
    cache_info1 = _fetch_info.cache_info()
    hits_before = cache_info1.hits

    # Second request
    res2 = client.post('/info', json={'url': url})
    assert res2.status_code == 200
    assert res2.json == data1

    cache_info2 = _fetch_info.cache_info()
    assert cache_info2.hits == hits_before + 1

def test_clip_validation(client):
    # Missing URL
    res = client.post('/clip', json={})
    assert res.status_code == 400
    assert 'error' in res.json

    # Duration > 185s
    res = client.post('/clip', json={'url': 'http://example.com', 'start': 0, 'end': 200})
    assert res.status_code == 400
    assert res.json['error'] == 'Max 3 minutes allowed'
