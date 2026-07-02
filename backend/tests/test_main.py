from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}


def test_list_events_and_create_event():
    response = client.get('/events')
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)

    create_response = client.post(
        '/events',
        json={
            'name': 'Winter Market',
            'description': 'A short test event',
            'location': 'Assen',
            'event_date': '2026-12-01',
            'organizer': 'Test Organizer',
            'category': 'Market',
            'expected_revenue': 500,
            'expected_attendance': 80,
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created['name'] == 'Winter Market'
    assert created['location'] == 'Assen'
