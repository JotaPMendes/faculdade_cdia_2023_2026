def test_contrato_get_prato(client):
    response = client.get("/pratos/1")
    assert response.status_code == 200
    prato = response.json()

    campos_obrigatorios = {"id", "nome", "categoria", "preco", "disponivel"}
    assert campos_obrigatorios.issubset(prato.keys())

    assert isinstance(prato["id"], int)
    assert isinstance(prato["nome"], str)
    assert isinstance(prato["categoria"], str)
    assert isinstance(prato["preco"], (int, float))
    assert isinstance(prato["disponivel"], bool)
    assert prato["preco"] > 0


def test_contrato_post_prato(client):
    response = client.post(
        "/pratos",
        json={"nome": "Prato Contrato CI 123", "categoria": "massa", "preco": 45.0},
    )
    assert response.status_code in [200, 201]
    prato = response.json()

    campos_obrigatorios = {
        "id",
        "nome",
        "categoria",
        "preco",
        "preco_promocional",
        "descricao",
        "disponivel",
        "criado_em",
    }
    assert campos_obrigatorios.issubset(prato.keys())
    assert isinstance(prato["id"], int)
    assert isinstance(prato["criado_em"], str)


def test_contrato_erro_404(client):
    response = client.get("/pratos/9999")
    assert response.status_code == 404
    corpo = response.json()

    assert "erro" in corpo
    assert isinstance(corpo["erro"], str)
    assert len(corpo["erro"]) > 0
    assert "status" in corpo
    assert corpo["status"] == 404
    assert "detalhes" in corpo
    assert isinstance(corpo["detalhes"], list)


def test_contrato_erro_422(client):
    response = client.post("/pratos", json={"nome": "X", "preco": -1})
    assert response.status_code == 422
    corpo = response.json()

    assert "erro" in corpo
    assert "detalhes" in corpo
    assert isinstance(corpo["detalhes"], list)
    assert len(corpo["detalhes"]) > 0

    for erro in corpo["detalhes"]:
        assert "campo" in erro
        assert "mensagem" in erro
        assert isinstance(erro["campo"], str)
        assert isinstance(erro["mensagem"], str)