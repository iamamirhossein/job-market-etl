from fastapi.testclient import TestClient

from app.api.deps import get_lake
from pipeline.lake.client import LakeClient


class FakeLake:
    def __init__(self, reachable: bool) -> None:
        self._reachable = reachable

    def is_reachable(self) -> bool:
        return self._reachable


def test_ready_when_lake_is_reachable(client: TestClient) -> None:
    fake: LakeClient = FakeLake(True)  # type: ignore[assignment]
    client.app.dependency_overrides[get_lake] = lambda: fake  # type: ignore[attr-defined]

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "checks": {"lake": True}}


def test_not_ready_when_lake_is_down(client: TestClient) -> None:
    fake: LakeClient = FakeLake(False)  # type: ignore[assignment]
    client.app.dependency_overrides[get_lake] = lambda: fake  # type: ignore[attr-defined]

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready", "checks": {"lake": False}}
