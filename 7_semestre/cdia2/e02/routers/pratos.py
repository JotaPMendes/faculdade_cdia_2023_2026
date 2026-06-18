from fastapi import APIRouter, HTTPException
from models.prato import DisponibilidadeInput, PratoInput, PratoOutput
from typing import Optional
from datetime import datetime
from pathlib import Path
import json
from copy import deepcopy
from config import settings

router = APIRouter()

_seed_pratos = [
    {"id": 1, "nome": "Niguiri de Salmão", "categoria": "japonesa", "preco": 45.0, "disponivel": True, "criado_em": datetime.now().isoformat()},
    {"id": 2, "nome": "Tempurá de Vegetais", "categoria": "japonesa", "preco": 38.0, "disponivel": True, "criado_em": datetime.now().isoformat()},
    {"id": 3, "nome": "Sushi Variado", "categoria": "japonesa", "preco": 60.0, "disponivel": False, "criado_em": datetime.now().isoformat()},
    {"id": 4, "nome": "Ramen", "categoria": "japonesa", "preco": 35.0, "disponivel": True, "criado_em": datetime.now().isoformat()},
    {"id": 5, "nome": "Gyoza", "categoria": "japonesa", "preco": 28.0, "disponivel": True, "criado_em": datetime.now().isoformat()},
    {"id": 6, "nome": "Mochi", "categoria": "japonesa", "preco": 15.0, "disponivel": False, "criado_em": datetime.now().isoformat()},
]


def _store_path() -> Path:
    return Path(settings.pratos_store_file)


def _load_pratos() -> list[dict]:
    if not settings.persist_pratos:
        return deepcopy(_seed_pratos)

    store_path = _store_path()
    if store_path.exists():
        with store_path.open("r", encoding="utf-8") as arquivo:
            return json.load(arquivo)

    store_path.parent.mkdir(parents=True, exist_ok=True)
    pratos_iniciais = deepcopy(_seed_pratos)
    with store_path.open("w", encoding="utf-8") as arquivo:
        json.dump(pratos_iniciais, arquivo, ensure_ascii=False, indent=2)
    return pratos_iniciais


def _save_pratos(pratos_atuais: list[dict]) -> None:
    if not settings.persist_pratos:
        return

    store_path = _store_path()
    store_path.parent.mkdir(parents=True, exist_ok=True)
    with store_path.open("w", encoding="utf-8") as arquivo:
        json.dump(pratos_atuais, arquivo, ensure_ascii=False, indent=2)


pratos = _load_pratos()

@router.get("/")
async def listar_pratos(
    categoria: Optional[str] = None,
    preco_maximo: Optional[float] = None,
    apenas_disponiveis: bool = False
):
    resultado = pratos
    if categoria:
        resultado = [prato for prato in resultado if prato["categoria"] == categoria]
    if preco_maximo is not None:
        resultado = [prato for prato in resultado if prato["preco"] <= preco_maximo]
    if apenas_disponiveis:
        resultado = [prato for prato in resultado if prato["disponivel"]]
    return resultado

@router.get("/{prato_id}")
async def buscar_prato(prato_id: int, formato: str = "completo"):
    for prato in pratos:
        if prato["id"] == prato_id:
            if formato == "resumido":
                return {"nome" : prato["nome"], "preco" : prato["preco"]}
            return prato
    raise HTTPException(
        status_code = 404,
        detail= f"Prato com id {prato_id} não encontrado"
    )

@router.post("/", response_model=PratoOutput)
async def criar_prato(prato: PratoInput):
    novo_id = max(p["id"] for p in pratos) + 1
    novo_prato = {
        "id": novo_id, 
        "criado_em": datetime.now().isoformat(),
        **prato.model_dump()}
    pratos.append(novo_prato)
    _save_pratos(pratos)
    return novo_prato

@router.post("/{prato_id}/aplicar_desconto")
async def aplicar_desconto(prato_id: int, percentual: float):
    prato = next((p for p in pratos if p["id"] == prato_id), None)
    if not prato:
        raise HTTPException(status_code=404, detail="Prato não encontrado")

    if percentual <= 0 or percentual > 50:
        raise HTTPException(
            status_code=400,
            detail="Percentual de desconto deve estar entre 1% e 50%"
        )

    if not prato["disponivel"]:
        raise HTTPException(
            status_code=400,
            detail="Não é possível aplicar desconto em prato indisponível"
        )

    prato["preco"] = prato["preco"] * (1 - percentual / 100)
    _save_pratos(pratos)
    return prato

@router.put("/{prato_id}/disponibilidade")
async def alterar_disponibilidade(prato_id: int, body: DisponibilidadeInput):
    for prato in pratos:
        if prato["id"] == prato_id:
            prato["disponivel"] = body.disponivel
            _save_pratos(pratos)
            return prato
    raise HTTPException(status_code=404, detail="Prato não encontrado")