from models.pedido import PedidoInput, PedidoOutput
from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime
from routers.pratos import pratos

router = APIRouter()

pedidos = [] 

@router.post("/", response_model=PedidoOutput)
async def criar_pedido(pedido: PedidoInput):
    prato = next((p for p in pratos if p["id"] == pedido.prato_id), None)

    if not prato:
        raise HTTPException(status_code=404, detail="Prato não encontrado")

    if not prato["disponivel"]:
        raise HTTPException(
            status_code=400,
            detail=f"O prato '{prato['nome']}' não está disponível no momento"
        )
    novo_id = len(pedidos) + 1 
    novo_pedido = {
        "id": novo_id,
        "prato_id": pedido.prato_id,
        "nome_prato": prato["nome"],
        "quantidade": pedido.quantidade,
        "valor_total": prato["preco"] * pedido.quantidade,
        "observacao": pedido.observacao
    }
    pedidos.append(novo_pedido)
    return novo_pedido