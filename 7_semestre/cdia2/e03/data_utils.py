from typing import Tuple

import numpy as np
import pandas as pd
from sklearn.datasets import make_classification


def gerar_dataset(
    n_samples: int = 2000,
    seed: int = 42,
    proporcao_positivos: float = 0.15,
) -> Tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """
    Gera dataset sintético de fraude usando make_classification.

    Parâmetros
    ----------
    n_samples : int
        Número de amostras a gerar.
    seed : int
        Seed para reprodutibilidade.
    proporcao_positivos : float
        Proporção da classe positiva. Deve estar entre 0.05 e 0.95.

    Retorna
    -------
    df : pd.DataFrame
        Dataset completo com features e target.
    X : np.ndarray
        Matriz de features.
    y : np.ndarray
        Vetor de targets.

    Exemplo
    -------
    >>> df, X, y = gerar_dataset(n_samples=500, seed=0)
    >>> df.shape
    (500, 7)
    """
    if not (0.05 <= proporcao_positivos <= 0.95):
        raise ValueError("proporcao_positivos deve estar entre 0.05 e 0.95")

    x_lat, y = make_classification(
        n_samples=n_samples,
        n_features=6,
        n_informative=4,
        n_redundant=1,
        n_repeated=0,
        n_classes=2,
        weights=[1 - proporcao_positivos, proporcao_positivos],
        class_sep=1.1,
        flip_y=0.01,
        random_state=seed,
    )

    rng = np.random.default_rng(seed)

    valor_transacao = np.clip(np.exp(3.0 + 0.9 * x_lat[:, 0]), 5, 20000).round(2)
    hora_base = rng.integers(0, 24, size=n_samples)
    madrugada_fraude = (y == 1) & (rng.random(n_samples) < 0.35)
    hora_base[madrugada_fraude] = rng.choice([0, 1, 2, 3, 4], size=madrugada_fraude.sum())
    hora_transacao = hora_base.astype(int)
    distancia_ultima_compra = np.clip(np.exp(2.1 + 0.7 * x_lat[:, 1]), 0, 5000).round(1)
    tentativas_senha = np.clip((1.5 + 2.0 * x_lat[:, 2]).round(), 1, 10).astype(int)
    prob_pais_diff = np.where(y == 1, 0.35, 0.06)
    pais_diferente = (rng.random(n_samples) < prob_pais_diff).astype(int)
    device_risk_score = (1 / (1 + np.exp(-1.8 * x_lat[:, 3]))).round(4)

    df = pd.DataFrame(
        {
            "valor_transacao": valor_transacao,
            "hora_transacao": hora_transacao,
            "distancia_ultima_compra": distancia_ultima_compra,
            "tentativas_senha": tentativas_senha,
            "pais_diferente": pais_diferente,
            "device_risk_score": device_risk_score,
            "fraude": y,
        }
    )

    x = df.drop(columns=["fraude"]).values
    y = df["fraude"].values
    return df, x, y