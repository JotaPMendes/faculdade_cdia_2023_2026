import os

import numpy as np
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from model_utils import load_model


router = APIRouter()

REPO_ID = os.getenv("HF_REPO_ID", "")
_model = None


def get_model():
	global _model
	if _model is None:
		if os.path.exists("model.pkl"):
			from model_utils import carregar_modelo

			_model = carregar_modelo("model.pkl")
		else:
			if not REPO_ID:
				raise ValueError("Defina HF_REPO_ID no ambiente para carregar do Hugging Face Hub")
			_model = load_model(REPO_ID)
	return _model


class PredictInput(BaseModel):
	valor_transacao: float = Field(gt=0, description="Valor em reais")
	hora_transacao: int = Field(ge=0, le=23, description="Hora do dia")
	distancia_ultima_compra: float = Field(ge=0, description="Distância em km")
	tentativas_senha: int = Field(ge=1, description="Tentativas de senha")
	pais_diferente: int = Field(ge=0, le=1, description="1 se país diferente")
	device_risk_score: float = Field(ge=0, le=1, description="Score de risco do dispositivo")


class PredictOutput(BaseModel):
	prediction: int
	probability: float
	label: str
	model_version: str


@router.post("/predict", response_model=PredictOutput)
async def predict(payload: PredictInput):
	model = get_model()

	features = np.array(
		[[
			payload.valor_transacao,
			payload.hora_transacao,
			payload.distancia_ultima_compra,
			payload.tentativas_senha,
			payload.pais_diferente,
			payload.device_risk_score,
		]]
	)

	prediction = int(model.predict(features)[0])
	probability = float(model.predict_proba(features)[0][1])
	label = "fraude" if prediction == 1 else "legitimo"

	return PredictOutput(
		prediction=prediction,
		probability=round(probability, 4),
		label=label,
		model_version=REPO_ID or "local:model.pkl",
	)


@router.get("/health")
async def health():
	try:
		model = get_model()
		test_input = np.zeros((1, 6))
		model.predict(test_input)
		body = {
			"api": "ok",
			"model": "ok",
			"model_repo": REPO_ID or "local:model.pkl",
			"detail": None,
		}
		return JSONResponse(content=body, status_code=200)
	except Exception as exc:
		body = {
			"api": "ok",
			"model": "degraded",
			"model_repo": REPO_ID or "local:model.pkl",
			"detail": str(exc),
		}
		return JSONResponse(content=body, status_code=503)
