from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def prato_valido():
    return {
        "nome": "Prato de Teste",
        "categoria": "massa",
        "preco": 42.0,
        "disponivel": True,
    }


@pytest.fixture
def bebida_valida():
    return {
        "nome": "Bebida de Teste",
        "tipo": "suco",
        "preco": 12.0,
        "alcoolica": False,
        "volume_ml": 300,
    }