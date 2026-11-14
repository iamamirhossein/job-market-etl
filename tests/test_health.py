from fastapi.testclient import TestClient

from app.schemas.health import HealthResponse


def test_get_health_success(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"] == "9.9.9"


def test_get_health_scheme(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    HealthResponse.model_validate(response.json())
