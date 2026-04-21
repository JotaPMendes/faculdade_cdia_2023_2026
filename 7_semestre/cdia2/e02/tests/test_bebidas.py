def test_listar_bebidas_retorna_200_e_lista(client):
    response = client.get("/bebidas")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_filtro_por_tipo_retorna_apenas_tipo_correto(client):
    response = client.get("/bebidas?tipo=vinho")
    assert response.status_code == 200
    bebidas = response.json()
    assert len(bebidas) > 0
    assert all(bebida["tipo"] == "vinho" for bebida in bebidas)


def test_filtro_por_alcoolica_retorna_apenas_alcoolicas(client):
    response = client.get("/bebidas?alcoolica=true")
    assert response.status_code == 200
    bebidas = response.json()
    assert len(bebidas) > 0
    assert all(bebida["alcoolica"] is True for bebida in bebidas)


def test_buscar_bebida_existente_retorna_200(client):
    response = client.get("/bebidas/1")
    assert response.status_code == 200
    bebida = response.json()
    assert "id" in bebida
    assert "nome" in bebida
    assert "preco" in bebida


def test_buscar_bebida_inexistente_retorna_404(client):
    response = client.get("/bebidas/9999")
    assert response.status_code == 404


def test_criar_bebida_valida(client):
    nome_unico = "Suco Teste CI 77701"
    response = client.post(
        "/bebidas",
        json={
            "nome": nome_unico,
            "tipo": "suco",
            "preco": 13.0,
            "alcoolica": False,
            "volume_ml": 350,
        },
    )
    assert response.status_code in [200, 201]
    dados = response.json()
    assert dados["nome"] == nome_unico
    assert dados["tipo"] == "suco"


def test_criar_bebida_com_tipo_invalido_retorna_422(client):
    response = client.post(
        "/bebidas",
        json={
            "nome": "Bebida Invalida",
            "tipo": "cha",
            "preco": 10.0,
            "alcoolica": False,
            "volume_ml": 300,
        },
    )
    assert response.status_code == 422


def test_criar_bebida_com_volume_invalido_retorna_422(client):
    response = client.post(
        "/bebidas",
        json={
            "nome": "Bebida Volume Invalido",
            "tipo": "suco",
            "preco": 10.0,
            "alcoolica": False,
            "volume_ml": 10,
        },
    )
    assert response.status_code == 422