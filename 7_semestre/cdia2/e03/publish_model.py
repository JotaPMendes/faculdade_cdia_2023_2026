import os
from pathlib import Path

import joblib
import numpy as np
import sklearn
from huggingface_hub import HfApi, login


MODEL_CARD_TEMPLATE = """---
language: pt
tags:
  - sklearn
  - classification
  - fraud-detection
  - mlops
---

# mlops-fraud-v1

Modelo de classificação binária para detecção de transações fraudulentas.

## Uso

```python
from huggingface_hub import hf_hub_download
import joblib

model = joblib.load(hf_hub_download(\"{repo_id}\", \"model.pkl\"))
features = [[250.0, 14, 12.5, 1, 0, 0.3]]
prediction = model.predict(features)
```

## Features de entrada

| Feature                 | Tipo  | Descrição                              |
|-------------------------|-------|----------------------------------------|
| valor_transacao         | float | Valor da transação em reais            |
| hora_transacao          | int   | Hora do dia (0-23)                     |
| distancia_ultima_compra | float | Distância geográfica em km             |
| tentativas_senha        | int   | Tentativas de senha antes da transação |
| pais_diferente          | int   | 1 se país diferente do cadastro        |
| device_risk_score       | float | Score de risco do dispositivo (0-1)    |

## Métricas (test set, 20% dos dados)

- Precision (fraude): 0.90
- Recall (fraude): 0.64
- F1 (fraude): 0.75

## Dependências

- scikit-learn=={sklearn_version}
- joblib=={joblib_version}
- numpy=={numpy_version}

## Limitações

Modelo treinado com dados sintéticos. Não deve ser usado em produção sem
retreinamento com dados reais e validação adequada.
"""


def carregar_env_local(caminho_env: str = ".env") -> None:
    env_path = Path(caminho_env)
    if not env_path.exists():
        return

    for linha in env_path.read_text(encoding="utf-8").splitlines():
        texto = linha.strip()
        if not texto or texto.startswith("#") or "=" not in texto:
            continue

        chave, valor = texto.split("=", 1)
        chave = chave.strip()
        valor = valor.strip().strip('"').strip("'")

        if chave and chave not in os.environ:
            os.environ[chave] = valor


def main() -> None:
    carregar_env_local()
    token = os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_TOKEN")
    if not token:
        raise ValueError("Defina HF_TOKEN ou HUGGING_FACE_TOKEN no ambiente")

    login(token=token)
    api = HfApi()
    username = api.whoami()["name"]
    repo_id = os.getenv("HF_REPO_ID") or f"{username}/mlops-fraud-v1"

    api.create_repo(repo_id=repo_id, repo_type="model", exist_ok=True, private=False)

    readme_path = Path("README.md")
    requirements_path = Path("requirements.txt")
    model_path = Path("model.pkl")

    if not model_path.exists():
        raise FileNotFoundError("Arquivo model.pkl nao encontrado. Execute train.py primeiro.")

    readme_content = MODEL_CARD_TEMPLATE.format(
        repo_id=repo_id,
        sklearn_version=sklearn.__version__,
        joblib_version=joblib.__version__,
        numpy_version=np.__version__,
    )
    readme_path.write_text(readme_content, encoding="utf-8")

    requirements_content = (
        f"scikit-learn=={sklearn.__version__}\n"
        f"joblib=={joblib.__version__}\n"
        f"numpy=={np.__version__}\n"
    )
    requirements_path.write_text(requirements_content, encoding="utf-8")

    for filename in ["model.pkl", "README.md", "requirements.txt"]:
        api.upload_file(
            path_or_fileobj=filename,
            path_in_repo=filename,
            repo_id=repo_id,
            repo_type="model",
            commit_message=f"chore: add {filename}",
        )
        print(f"Publicado: {filename}")

    print(f"Repositorio: https://huggingface.co/{repo_id}")


if __name__ == "__main__":
    main()