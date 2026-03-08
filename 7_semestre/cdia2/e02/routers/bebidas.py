from models.bebida import BebidaInput, BebidaOutput
from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime

router = APIRouter()

bebidas = [
    {"id": 1, "nome": "Água Mineral", "tipo": "agua", "preco": 8.0, "alcoolica": False, "volume_ml": 500, "criado_em": "2024-01-01T00:00:00"},
    {"id": 2, "nome": "Chianti Classico", "tipo": "vinho", "preco": 120.0, "alcoolica": True, "volume_ml": 750, "criado_em": "2024-01-01T00:00:00"},
    {"id": 3, "nome": "San Pellegrino", "tipo": "agua", "preco": 15.0, "alcoolica": False, "volume_ml": 750, "criado_em": "2024-01-01T00:00:00"},
    {"id": 4, "nome": "Suco de Laranja", "tipo": "suco", "preco": 18.0, "alcoolica": False, "volume_ml": 300, "criado_em": "2024-01-01T00:00:00"},
    {"id": 5, "nome": "Prosecco", "tipo": "vinho", "preco": 95.0, "alcoolica": True, "volume_ml": 750, "criado_em": "2024-01-01T00:00:00"},
]

@router.get("/", response_model=list[BebidaOutput])
async def listar_bebidas(
    tipo: Optional[str] = None,
    alcoolica: Optional[bool] = None
):
    resultado = bebidas
    if tipo:
        resultado = [b for b in resultado if b["tipo"] == tipo]
    if alcoolica is not None:
        resultado = [b for b in resultado if b["alcoolica"] == alcoolica]
    return resultado

@router.get("/{bebida_id}")
async def buscar_bebida(bebida_id: int):
    for bebida in bebidas:
        if bebida["id"] == bebida_id:
            return bebida
    raise HTTPException(
        status_code=404, 
        detail=f"Bebida com id {bebida_id} não encontrada"
    )

@router.post("/", response_model=BebidaOutput)
async def criar_bebida(bebida: BebidaInput):
    novo_id = max(b["id"] for b in bebidas) + 1
    nova_bebida = {
        "id": novo_id,
        "criado_em": datetime.now().isoformat(),
        **bebida.model_dump()
    }
    bebidas.append(nova_bebida)
    return nova_bebida