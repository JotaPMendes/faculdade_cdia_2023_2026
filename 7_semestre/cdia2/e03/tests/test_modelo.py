import os

import numpy as np
import pytest

from model_utils import load_model

REPO_ID = os.getenv("HF_REPO_ID", "")

PAYLOAD_VALIDO = {
    "valor_transacao": 250.0,
    "hora_transacao": 14,
    "distancia_ultima_compra": 12.5,
    "tentativas_senha": 1,
    "pais_diferente": 0,
    "device_risk_score": 0.3,
}


@pytest.fixture(scope="module")
def modelo_hf():
    if not REPO_ID:
        pytest.skip("HF_REPO_ID não configurado para testes de integração")
    return load_model(REPO_ID)


@pytest.fixture
def amostra_valida():
    return np.array([[250.0, 14, 12.5, 1, 0, 0.3]])


@pytest.mark.integracao
def test_modelo_carrega_do_hub(modelo_hf):
    assert modelo_hf is not None


@pytest.mark.integracao
def test_modelo_tem_predict_e_predict_proba(modelo_hf):
    assert hasattr(modelo_hf, "predict")
    assert callable(modelo_hf.predict)
    assert hasattr(modelo_hf, "predict_proba")
    assert callable(modelo_hf.predict_proba)


@pytest.mark.integracao
def test_predict_modelo_formato_saida(modelo_hf, amostra_valida):
    pred = modelo_hf.predict(amostra_valida)
    prob = modelo_hf.predict_proba(amostra_valida)
    assert pred.shape == (1,)
    assert pred[0] in [0, 1]
    assert prob.shape[0] == 1
    assert 0.0 <= float(prob[0][1]) <= 1.0


@pytest.mark.integracao
def test_predict_endpoint_retorna_200(client):
    response = client.post("/ml/predict", json=PAYLOAD_VALIDO)
    assert response.status_code == 200


@pytest.mark.integracao
def test_predict_endpoint_contrato(client):
    response = client.post("/ml/predict", json=PAYLOAD_VALIDO)
    assert response.status_code == 200
    body = response.json()
    assert "prediction" in body
    assert "probability" in body
    assert "label" in body
    assert "model_version" in body
    assert body["prediction"] in [0, 1]
    assert isinstance(body["probability"], float)
    assert 0.0 <= body["probability"] <= 1.0
    assert isinstance(body["label"], str)
    assert len(body["label"]) > 0


@pytest.mark.integracao
def test_predict_sem_campo_obrigatorio_retorna_422(client):
    response = client.post("/ml/predict", json={"valor_transacao": 100.0})
    assert response.status_code == 422


@pytest.mark.integracao
@pytest.mark.parametrize(
    "campo,valor_invalido",
    [
        ("hora_transacao", 25),
        ("hora_transacao", -1),
        ("tentativas_senha", 0),
        ("valor_transacao", -50.0),
        ("device_risk_score", 1.5),
    ],
)
def test_predict_campo_invalido_retorna_422(client, campo, valor_invalido):
    payload = {**PAYLOAD_VALIDO, campo: valor_invalido}
    response = client.post("/ml/predict", json=payload)
    assert response.status_code == 422
