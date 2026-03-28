from __future__ import annotations

from datetime import datetime, timedelta

from pydantic import BaseModel, Field, field_validator

from config import settings


class ReservaInput(BaseModel):
    mesa: int = Field(ge=1, le=settings.max_mesas)
    nome: str = Field(min_length=2, max_length=100)
    pessoas: int = Field(ge=1, le=settings.max_pessoas_por_mesa)
    horario: datetime = Field()

    @field_validator("horario")
    def exige_antecedencia_minima(cls, valor: datetime) -> datetime:
        minimo = datetime.now() + timedelta(hours=1)
        if valor <= minimo:
            raise ValueError("Reservas devem ser feitas com pelo menos 1 hora de antecedência")
        return valor


class ReservaOutput(BaseModel):
    id: int
    mesa: int
    nome: str
    pessoas: int
    horario: datetime
    ativa: bool
    criada_em: str
