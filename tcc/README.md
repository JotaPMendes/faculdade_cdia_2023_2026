# Comparação PINN vs ML Clássico vs FEM

Este projeto implementa uma comparação sistemática entre **Physics-Informed Neural Networks (PINNs)**, **Métodos Numéricos (FEM)** e **Machine Learning Clássico (Random Forest, XGBoost, etc.)** para resolver Equações Diferenciais Parciais (EDPs).

## 🚀 Funcionalidades

- **Problemas Suportados**:
  - `poisson_2d`: Equação de Poisson em domínio quadrado (Analítico).
  - `heat_1d`: Equação do Calor 1D (Temporal).
  - `wave_1d`: Equação da Onda 1D (Temporal).
  - `electrostatic_mesh`: Problema Eletrostático em malha complexa (`.msh`).

- **Comparação Justa**:
  - Geração de dados de treino/teste consistente.
  - Métricas de erro absoluto (MAE) e R².
  - Visualizações detalhadas (Mapas de Contorno e Séries Temporais).

- **Configuração Dinâmica**:
  - Ajuste automático de domínio baseado na malha carregada.
  - Controle de iterações de treino e checkpoints.
  - Flag `use_mesh` para desacoplar lógica de malha de problemas analíticos.

## 📦 Instalação

1. Crie um ambiente virtual:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

## 🛠️ Como Usar

### 1. Configuração (`config.py`)
Edite o arquivo `config.py` para selecionar o problema e ajustar parâmetros:

```python
CONFIG = {
    "problem": "electrostatic_mesh", # ou "poisson_2d", "heat_1d", "wave_1d"
    "mesh_file": "domain.msh",       # Para problemas com malha
    "Lx": 1.0,                       # Domínio padrão (sobrescrito se usar malha)
    "use_mesh": False,               # True para carregar .msh, False para analítico
    ...
}
```

### 2. Executar Treinamento e Comparação
```bash
python3 main.py
```
Isso irá:
1. Carregar/Criar o problema.
2. Treinar a PINN (com checkpoints automáticos).
3. Resolver via FEM (se aplicável).
4. Treinar modelos de ML Clássico.
5. Gerar métricas (`metrics.json`) e gráficos (`comparison.png`).

### 3. Gerar Relatórios
Para gerar um relatório consolidado em Markdown:
```bash
python3 generate_report.py --problem electrostatic_mesh --run run_001
```

## 📊 Estrutura do Projeto

- `main.py`: Script principal de orquestração.
- `config.py`: Configurações globais.
- `problems/`: Definições das EDPs e Geometrias.
- `models/`: Implementações da PINN, FEM e Wrappers de ML.
- `utils/`:
  - `data.py`: Geração de dados sintéticos e amostragem.
  - `plots.py`: Visualização dos resultados.
  - `mesh_loader.py`: Carregamento robusto de arquivos `.msh`.
  - `checkpoint.py`: Gerenciamento de salvamento/carregamento de modelos.
- `checkpoints/`: Onde os modelos, métricas e gráficos são salvos.

## 📝 Notas sobre Malhas (Mesh)
Para problemas como `electrostatic_mesh`, o sistema ajusta automaticamente o domínio (`Lx`, `Ly`, `train_box`) com base nas dimensões reais do arquivo `.msh`. Certifique-se de que a flag `use_mesh` está ativada no problema (o `electrostatic_mesh.py` já faz isso por padrão).
