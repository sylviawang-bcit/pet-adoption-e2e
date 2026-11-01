import pytest
from web import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


def test_form_submit_success(client):
    response = client.post("/Forms", data={
        "name": "Test User",
        "email": "test@email.com",
        "phone": "6041234567",
        "reason": "Adoption",
        "message": "Hello"
    })

    assert response.status_code == 200
    assert b"success" in response.data


def test_form_submit_missing_fields(client):
    response = client.post("/Forms", data={
        "name": "",
        "email": "",
        "phone": "",
        "reason": "",
        "message": ""
    })

    assert response.status_code == 400