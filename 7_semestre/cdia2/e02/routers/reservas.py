from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from fastapi import APIRouter, HTTPException

from models.reserva import ReservaInput, ReservaOutput

router = APIRouter()

reservas = [
    {
        "id": 1,
        "mesa": 5,
        "nome": "Silva",
        "pessoas": 4,
        "horario": datetime(2026, 3, 8, 18, 0),
        "ativa": True,
        "criada_em": "2026-03-01T10:00:00",
    },
    {
        "id": 2,
        "mesa": 3,
        "nome": "Costa",
        "pessoas": 2,
        "horario": datetime(2026, 3, 8, 19, 30),
        "ativa": True,
        "criada_em": "2026-03-01T11:00:00",
    },
]


def mesma_data(h1: datetime, h2: datetime) -> bool:
    return h1.date() == h2.date()


def buscar_reserva_por_id(reserva_id: int) -> dict | None:
    for reserva in reservas:
        if reserva["id"] == reserva_id:
            return reserva
    return None


@router.get("/", response_model=list[ReservaOutput])
async def listar_reservas(
    data: date | None = None,
    status: Literal["ativa", "cancelada"] | None = None,
):
    resultado = reservas
    if status is None:
        resultado = [r for r in resultado if r["ativa"]]
    else:
        ativo = status == "ativa"
        resultado = [r for r in resultado if r["ativa"] == ativo]
    if data:
        resultado = [r for r in resultado if r["horario"].date() == data]
    return resultado


@router.get("/mesa/{numero}", response_model=list[ReservaOutput])
async def listar_reservas_mesa(numero: int):
    return [r for r in reservas if r["mesa"] == numero]


@router.get("/{reserva_id}", response_model=ReservaOutput)
async def buscar_reserva(reserva_id: int):
    reserva = buscar_reserva_por_id(reserva_id)
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva não encontrada")
    return reserva


@router.post("/", response_model=ReservaOutput)
async def criar_reserva(reserva: ReservaInput):
    for existente in reservas:
        if (
            existente["mesa"] == reserva.mesa
            and existente["ativa"]
            and mesma_data(existente["horario"], reserva.horario)
        ):
            raise HTTPException(
                status_code=400,
                detail="Já existe uma reserva ativa para essa mesa hoje",
            )
    nova_reserva = {
        "id": len(reservas) + 1,
        **reserva.model_dump(),
        "ativa": True,
        "criada_em": datetime.now().isoformat(),
    }
    reservas.append(nova_reserva)
    return nova_reserva


@router.delete("/{reserva_id}")
async def cancelar_reserva(reserva_id: int):
    reserva = buscar_reserva_por_id(reserva_id)
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva não encontrada")
    if not reserva["ativa"]:
        raise HTTPException(status_code=400, detail="Reserva já está cancelada")
    reserva["ativa"] = False
    return {"mensagem": "cancelada"}
