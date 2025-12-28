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
uv pip install -r requirements.txt
```

## 🛠️ Como Usar

### 1. Configuração (`config.py`)
Edite o arquivo `config.py` para selecionar o problema e ajustar parâmetros:

```python
CONFIG = {
    "problem": "electrostatic_mesh", # ou "poisson_2d", "heat_1d", "wave_1d"
    "mesh_file": "meshes/files/stator.msh", # Caminho para o arquivo .msh
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

### 3. Resultados (IMPORTANTE)
Todos os resultados da última execução são salvos automaticamente em:
👉 **`results/latest/`**

Lá você encontrará:
- `visualization.html`: Visualização interativa 3D (Abra este arquivo!).
- `report.md`: Relatório completo.
- `comparison.png`: Gráficos estáticos.
- `metrics.json`: Métricas de erro.

### 4. Gerar Relatórios (Opcional)
Para gerar um relatório consolidado em Markdown (também vai para `results/latest`):
```bash
python3 utils/generate_report.py
```

## 📊 Estrutura do Projeto

- `main.py`: Script principal de orquestração.
- `config.py`: Configurações globais.
- `results/latest/`: **ONDE ESTÃO OS RESULTADOS FINAIS.**
- `problems/`: Definições das EDPs e Geometrias.
- `models/`: Implementações da PINN, FEM e Wrappers de ML.
- `utils/`:
  - `data.py`: Geração de dados sintéticos e amostragem.
  - `plots.py`: Visualização dos resultados.
  - `mesh_loader.py`: Carregamento robusto de arquivos `.msh`.
  - `checkpoint.py`: Gerenciamento de salvamento/carregamento de modelos.
  - `view_mesh.py`: Visualizador de malhas pré-treino.
- `checkpoints/`: Histórico de execuções (Run 001, 002...).
- `meshes/`:
  - `files/`: Arquivos `.msh` (gerados pelo GMSH).
  - `images/`: Visualizações `.png` (geradas pelo `utils/view_mesh.py`).

## 📝 Notas sobre Malhas (Mesh)
As malhas devem ser organizadas na pasta `meshes/`:
- `meshes/files/`: Arquivos `.msh` (gerados pelo GMSH).
- `meshes/images/`: Visualizações `.png` (geradas pelo `utils/view_mesh.py`).

Para usar uma nova malha:
1. Coloque o arquivo `.msh` em `meshes/files/`.
2. Atualize `config.py` apontando para `meshes/files/seu_arquivo.msh`.
3. Rode `python utils/view_mesh.py` para gerar a visualização em `meshes/images/`.
