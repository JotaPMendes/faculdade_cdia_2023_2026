import os

import joblib
import numpy as np
from huggingface_hub import hf_hub_download


def salvar_modelo(model, caminho_arquivo: str = "model.pkl") -> None:
    joblib.dump(model, caminho_arquivo)


def carregar_modelo(caminho_arquivo: str = "model.pkl"):
    return joblib.load(caminho_arquivo)


def load_model(
    repo_id: str,
    filename: str = "model.pkl",
    force_download: bool = False,
):
    local_path = hf_hub_download(
        repo_id=repo_id,
        filename=filename,
        force_download=force_download,
    )
    return joblib.load(local_path)


def validar_predicoes_iguais(
    pred_original: np.ndarray, pred_carregado: np.ndarray
) -> None:
    if not np.array_equal(pred_original, pred_carregado):
        raise AssertionError("Predicoes divergem entre modelo original e carregado")


def tamanho_arquivo_kb(caminho_arquivo: str = "model.pkl") -> float:
    return os.path.getsize(caminho_arquivo) / 1024
