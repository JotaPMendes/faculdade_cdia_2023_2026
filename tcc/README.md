# 🔬 TCC - Comparação PINN vs ML Clássico

Projeto de TCC comparando **Physics-Informed Neural Networks (PINNs)** com métodos tradicionais de **Machine Learning** na resolução de EDPs (Equações Diferenciais Parciais).

## 📋 Descrição

Este projeto implementa e compara três diferentes problemas físicos:
1. **Equação do Calor 1D** - Difusão térmica
2. **Equação da Onda 1D** - Propagação de ondas
3. **Equação de Poisson 2D** - Problemas elípticos

## 🏗️ Estrutura do Projeto

```
tcc/
├── config.py                 # Configurações do experimento
├── main.py                   # Script principal de execução
├── test_integration.py       # Testes de integração
├── requirements.txt          # Dependências Python
├── models/
│   ├── pinn.py              # Treinamento do PINN
│   └── regressors.py        # Modelos ML Clássicos (RF, XGB, KNN)
├── problems/
│   ├── __init__.py          # Interface de problemas
│   ├── heat.py              # Equação do Calor
│   ├── wave.py              # Equação da Onda
│   └── poisson2d.py         # Equação de Poisson 2D
└── utils/
    ├── data.py              # Geração de dados
    └── plots.py             # Visualizações
```

## 🛠️ Tecnologias Utilizadas

- **DeepXDE** - Framework para PINNs
- **TensorFlow** - Backend para deep learning
- **scikit-learn** - Modelos de ML clássico
- **NumPy** - Computação numérica
- **Matplotlib** - Visualização de resultados

## 📦 Instalação

### 1. Criar ambiente virtual (opcional, mas recomendado)

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Verificar instalação

```bash
python test_integration.py
```

## 🚀 Uso

### Configuração

Edite o arquivo `config.py` para escolher o problema e parâmetros:

```python
CONFIG = {
    "problem": "poisson_2d",   # Opções: "heat_1d", "wave_1d", "poisson_2d"
    "alpha": 0.1,              # Difusividade (heat)
    "c": 1.0,                  # Velocidade da onda (wave)
    "Lx": 4.0,                 # Comprimento do domínio
    "T_train": 8.0,            # Tempo de treinamento
    "T_eval": 16.0,            # Tempo de avaliação
    "N_data": 5000,            # Amostras para ML
    "Nx_train": 60,            # Pontos em x (Poisson)
    "Ny_train": 60,            # Pontos em y (Poisson)
    "train_box": [0.0, 0.0, 0.6, 1.0]  # Região de treino [xmin, ymin, xmax, ymax]
}
```

### Execução

```bash
python main.py
```

## 📊 Problemas Implementados

### 1. Equação do Calor (heat_1d)

**Equação**: ∂u/∂t = α ∂²u/∂x²

**Condições**:
- Domínio: x ∈ [0, Lx], t ∈ [0, T]
- BC: u(0,t) = u(Lx,t) = 0
- IC: u(x,0) = sin(πx/Lx)

**Solução Analítica**: u(x,t) = sin(kx) exp(-αk²t), k = π/Lx

### 2. Equação da Onda (wave_1d)

**Equação**: ∂²u/∂t² = c² ∂²u/∂x²

**Condições**:
- Domínio: x ∈ [0, Lx], t ∈ [0, T]
- BC: u(0,t) = u(Lx,t) = 0
- IC: u(x,0) = sin(πx/Lx), ∂u/∂t(x,0) = 0

**Solução Analítica**: u(x,t) = sin(kx) cos(ckt), k = π/Lx

### 3. Equação de Poisson 2D (poisson_2d)

**Equação**: ∇²u = f

**Condições**:
- Domínio: [x,y] ∈ [0,1]²
- BC: u = 0 nas bordas
- Fonte: f = -2π² sin(πx) sin(πy)

**Solução Analítica**: u(x,y) = sin(πx) sin(πy)

## 🧪 Modelos Comparados

### PINN (Physics-Informed Neural Network)
- Rede neural profunda (4-5 camadas)
- Otimização: Adam + L-BFGS
- Incorpora física através de loss function
- Resampling de pontos durante treinamento

### ML Clássicos
- **Random Forest** (RF): 200 estimadores
- **Gradient Boosting** (XGB): 200 estimadores
- **K-Nearest Neighbors** (KNN): 10 vizinhos

## 📈 Métricas de Avaliação

- **MAE** (Mean Absolute Error): Erro médio absoluto
- **R² Score**: Coeficiente de determinação
- **Generalização**: Teste em regiões não vistas durante treino
  - Temporal: t > T_train (Heat/Wave)
  - Espacial: fora do train_box (Poisson)

## 🎯 Experimentos

### Teste de Generalização Temporal (Heat/Wave)
- **Treino**: t ∈ [0, T_train]
- **Teste**: t ∈ [T_train, T_eval]
- **Objetivo**: Verificar extrapolação temporal

### Teste de Generalização Espacial (Poisson)
- **Treino**: região restrita (train_box)
- **Teste**: fora da região de treino
- **Objetivo**: Verificar capacidade de generalização espacial

## 📊 Visualizações

O script gera automaticamente:

### Para problemas temporais (Heat/Wave):
- Gráficos de evolução temporal
- Comparação PINN vs ML vs Analítico
- Erros ao longo do tempo

### Para problemas espaciais (Poisson):
- Mapas de contorno 2D
- Comparação visual das soluções
- Caixa de treino destacada

## 🔧 Customização

### Adicionar novo problema

1. Crie arquivo em `problems/novo_problema.py`:
```python
import numpy as np
import deepxde as dde
import tensorflow as tf

def make_novo_problema(cfg):
    # Definir solução analítica
    def u_true(X):
        # ...
        return u
    
    # Definir EDP
    def pde(X, y):
        # ...
        return residual
    
    # Definir geometria e condições de contorno
    # ...
    
    return dict(kind="time" or "space", u_true=u_true, data=data, net=net)
```

2. Adicionar em `problems/__init__.py`:
```python
from .novo_problema import make_novo_problema

def make_problem(cfg):
    # ...
    elif cfg["problem"] == "novo_problema":
        return make_novo_problema(cfg)
```

## 📝 Resultados Esperados

O projeto gera:
1. **Métricas quantitativas**: MAE para cada modelo
2. **Ranking de modelos**: Ordenação por performance
3. **Visualizações**: Gráficos comparativos
4. **Checkpoint**: Modelo PINN salvo em `checkpoints/`

## 🐛 Troubleshooting

### Erro: ModuleNotFoundError
```bash
pip install -r requirements.txt
```

### Erro: Backend TensorFlow
```bash
export DDE_BACKEND=tensorflow.compat.v1
```

### GPU não detectada
- PINN funciona em CPU também (mais lento)
- Para GPU: instalar tensorflow-gpu

## 📚 Referências

- Raissi, M., Perdikaris, P., & Karniadakis, G. E. (2019). Physics-informed neural networks
- DeepXDE: A deep learning library for solving differential equations
- Scikit-learn: Machine Learning in Python

## 👥 Autor

Projeto de TCC - [Seu Nome]

## 📄 Licença

Este projeto é desenvolvido para fins acadêmicos.

---

**Status**: ✅ Todos os módulos testados e funcionando corretamente
