---
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

model = joblib.load(hf_hub_download("seu-usuario/mlops-fraud-v1", "model.pkl"))
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

- scikit-learn
- joblib
- numpy

## Limitações

Modelo treinado com dados sintéticos. Não deve ser usado em produção sem
retreinamento com dados reais e validação adequada.
