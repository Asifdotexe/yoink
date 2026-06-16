from fastapi.testclient import TestClient

from yoink.api.main import app

client = TestClient(app)


def test_api_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome to Yoink API" in response.json()["message"]


def test_api_sanitize():
    response = client.post(
        "/api/v1/sanitize",
        json={
            "content": "def foo():\n    # test comment\n    return 42",
            "file_extension": ".py",
        },
    )
    assert response.status_code == 200
    assert "test comment" not in response.json()["sanitized_content"]
