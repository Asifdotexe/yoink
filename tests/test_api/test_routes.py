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
    data = response.json()
    assert "test comment" not in data["sanitized_content"]
    assert "estimated_tokens" in data
    assert data["estimated_tokens"] > 0


def test_api_pack():
    response = client.post(
        "/api/v1/pack",
        json={
            "files": [
                {"path": "main.py", "content": "print('hello')"},
            ],
            "visualize": False,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "packed_content" in data
    assert data["total_files"] == 1
    assert "estimated_tokens" in data
    assert data["estimated_tokens"] > 0
