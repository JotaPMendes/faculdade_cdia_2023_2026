import pytest


@pytest.mark.smoke
def test_root_retorna_ok(client):
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"


@pytest.mark.smoke
def test_health_modelo_responde(client):
    response = client.get("/ml/health")
    assert response.status_code in [200, 503]
    body = response.json()
    assert "api" in body
    assert body["api"] == "ok"
    assert "model" in body
