def test_criar_pedido_com_prato_existente(client):
    client.put("/pratos/1/disponibilidade", json={"disponivel": True})
    payload = {"prato_id": 1, "quantidade": 2, "observacao": "sem cebola"}
    response = client.post("/pedidos", json=payload)
    assert response.status_code in [200, 201]
    dados = response.json()
    assert "valor_total" in dados
    assert "nome_prato" in dados


def test_valor_total_calculado_corretamente(client):
    client.put("/pratos/1/disponibilidade", json={"disponivel": True})
    prato = client.get("/pratos/1").json()
    preco_unitario = prato["preco"]
    payload = {"prato_id": 1, "quantidade": 3}
    response = client.post("/pedidos", json=payload)
    assert response.status_code in [200, 201]
    assert response.json()["valor_total"] == preco_unitario * 3


def test_criar_pedido_com_prato_inexistente_retorna_404(client):
    payload = {"prato_id": 9999, "quantidade": 1}
    response = client.post("/pedidos", json=payload)
    assert response.status_code == 404


def test_criar_pedido_com_prato_indisponivel_retorna_400(client):
    client.put("/pratos/1/disponibilidade", json={"disponivel": False})
    try:
        payload = {"prato_id": 1, "quantidade": 1}
        response = client.post("/pedidos", json=payload)
        assert response.status_code == 400
    finally:
        client.put("/pratos/1/disponibilidade", json={"disponivel": True})


def test_criar_pedido_com_quantidade_zero_retorna_422(client):
    payload = {"prato_id": 1, "quantidade": 0}
    response = client.post("/pedidos", json=payload)
    assert response.status_code == 422