import pytest


@pytest.mark.smoke
def test_listar_pratos_retorna_200_e_lista(client):
    response = client.get("/pratos")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_filtro_por_categoria_retorna_apenas_categoria_correta(client):
    response = client.get("/pratos?categoria=japonesa")
    assert response.status_code == 200
    pratos = response.json()
    assert len(pratos) > 0
    assert all(prato["categoria"] == "japonesa" for prato in pratos)


@pytest.mark.smoke
def test_buscar_prato_existente_retorna_campos_esperados(client):
    response = client.get("/pratos/1")
    assert response.status_code == 200
    prato = response.json()
    assert "id" in prato
    assert "nome" in prato
    assert "preco" in prato


def test_buscar_prato_inexistente_retorna_404(client):
    response = client.get("/pratos/9999")
    assert response.status_code == 404


@pytest.mark.smoke
def test_criar_prato_valido(client):
    nome_unico = "Massa Teste CI 91001"
    response = client.post(
        "/pratos",
        json={
            "nome": nome_unico,
            "categoria": "massa",
            "preco": 54.0,
            "disponivel": True,
        },
    )
    assert response.status_code in [200, 201]
    dados = response.json()
    assert dados["nome"] == nome_unico
    assert dados["preco"] == 54.0
    assert "id" in dados


@pytest.mark.validacao
def test_criar_prato_com_preco_negativo_retorna_422(client):
    response = client.post(
        "/pratos",
        json={"nome": "Prato Invalido", "categoria": "massa", "preco": -10.0},
    )
    assert response.status_code == 422


@pytest.mark.validacao
def test_criar_prato_com_nome_curto_retorna_422(client):
    response = client.post(
        "/pratos", json={"nome": "AB", "categoria": "massa", "preco": 40.0}
    )
    assert response.status_code == 422


@pytest.mark.validacao
@pytest.mark.parametrize(
    "categoria_invalida",
    ["esoterico", "fastfood", "japonesa", "PIZZA"],
)
def test_categoria_invalida_retorna_422(client, categoria_invalida):
    response = client.post(
        "/pratos",
        json={"nome": "Prato Teste", "categoria": categoria_invalida, "preco": 40.0},
    )
    assert response.status_code == 422


def test_prato_criado_aparece_na_listagem(client):
    nome_unico = "Tagliatelle Teste CI 99123"
    client.post(
        "/pratos",
        json={"nome": nome_unico, "categoria": "massa", "preco": 68.0},
    )
    response = client.get("/pratos")
    nomes = [p["nome"] for p in response.json()]
    assert nome_unico in nomes


@pytest.mark.parametrize("id_inexistente", [9999, 123456, 99999])
def test_prato_inexistente_retorna_404(client, id_inexistente):
    response = client.get(f"/pratos/{id_inexistente}")
    assert response.status_code == 404


@pytest.mark.parametrize(
    "categoria_valida",
    ["pizza", "massa", "sobremesa", "entrada", "salada"],
)
def test_filtro_por_categoria_valida(client, categoria_valida):
    response = client.get(f"/pratos?categoria={categoria_valida}")
    assert response.status_code == 200
    for prato in response.json():
        assert prato["categoria"] == categoria_valida