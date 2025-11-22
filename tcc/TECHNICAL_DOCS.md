# 📘 Documentação Técnica

Este documento detalha o funcionamento interno dos solvers e sistemas implementados neste projeto.

## 1. Solvers Implementados

### 1.1. Finite Element Method (FEM)
O solver FEM (`models/fem.py`) serve como **baseline numérico** de alta precisão para validar os resultados da PINN e dos modelos de ML.

*   **Tipo de Elemento**: Elementos finitos Q1 (bilineares) em uma malha estruturada retangular.
*   **Formulação Fraca**: Para a equação de Poisson $-\Delta u = f$, buscamos $u \in H^1_0(\Omega)$ tal que:
    $$ \int_\Omega \nabla u \cdot \nabla v \, dx = \int_\Omega f v \, dx, \quad \forall v \in H^1_0(\Omega) $$
*   **Montagem da Matriz**:
    *   A matriz de rigidez global $K$ é montada a partir das matrizes locais $K_e$ de cada elemento $4 \times 4$.
    *   Utiliza-se `scipy.sparse.coo_matrix` para montagem eficiente e `csr_matrix` para resolução.
*   **Condições de Contorno**:
    *   Dirichlet: Os nós da borda são identificados e suas linhas na matriz $K$ são substituídas por uma identidade (método da penalidade exata/substituição), forçando o valor $u = u_{true}$.

### 1.2. Physics-Informed Neural Networks (PINN)
A PINN (`models/pinn.py`) resolve a EDP minimizando uma função de perda composta pelos resíduos da equação e das condições de contorno.

*   **Framework**: DeepXDE com backend TensorFlow (compat.v1).
*   **Arquitetura**: `MsFFN` (Multi-scale Fourier Feature Network).
    *   Esta arquitetura é escolhida por sua capacidade superior em aprender funções com altas frequências, mitigando o "spectral bias" de redes neurais comuns.
*   **Função de Perda**:
    $$ \mathcal{L} = \lambda_{PDE} \mathcal{L}_{PDE} + \lambda_{BC} \mathcal{L}_{BC} $$
    *   $\mathcal{L}_{PDE}$: Média dos quadrados dos resíduos da equação diferencial nos pontos de colocação.
    *   $\mathcal{L}_{BC}$: Erro quadrático médio nos pontos de contorno.
*   **Otimização Híbrida**:
    1.  **Adam**: Otimizador estocástico robusto para as primeiras 15.000 iterações (exploração global).
    2.  **L-BFGS**: Otimizador de segunda ordem (quasi-Newton) para refinamento final (convergência rápida e precisa).

### 1.3. Machine Learning Clássico
Os modelos de ML (`models/regressors.py`) tratam o problema como uma regressão pura $f(x,y) \to u$.

*   **Dados**: Treinados apenas com pontos amostrados dentro do `train_box`.
*   **Modelos**:
    *   **Random Forest**: Ensemble de árvores de decisão. Bom para capturar não-linearidades, mas péssimo em extrapolação.
    *   **XGBoost**: Boosting de gradiente. Alta performance em interpolação.
    *   **KNN**: Baseado em vizinhança. Simples, mas sofre com a maldição da dimensionalidade e não extrapola bem.

## 2. Sistema de Checkpointing Avançado

O sistema (`utils/checkpoint.py`) gerencia a persistência dos modelos PINN de forma inteligente.

### 2.1. Registro (`registry.json`)
Mantém um mapeamento entre as configurações do experimento e os diretórios de salvamento.
*   **Hash de Configuração**: Cada conjunto de parâmetros em `config.py` gera um hash único MD5.
*   **Run ID**: O sistema atribui um ID sequencial (`run_001`, `run_002`) para cada configuração única.

### 2.2. Fluxo de Trabalho
1.  Ao iniciar o treino, o sistema calcula o hash da configuração atual.
2.  Verifica no `registry.json` se essa configuração já foi executada.
    *   **Sim**: Reutiliza o diretório existente e tenta retomar o treinamento (Resume).
    *   **Não**: Cria um novo diretório (`run_XXX`) e registra a nova configuração.
3.  **Resume Logic**: Se um checkpoint existe, o modelo carrega os pesos e treina apenas pelas iterações restantes (`total - current_step`).

### 2.3. Limpeza Automática
Para economizar espaço, o sistema mantém apenas os **3 checkpoints mais recentes** em cada diretório de execução.

## 3. Metodologia de Comparação

A comparação é realizada em três níveis:

1.  **Física (Ground Truth)**: Solução analítica exata.
2.  **Numérica (FEM)**: Aproximação tradicional de alta ordem. Serve para validar se a PINN está convergindo para a solução física correta.
3.  **Dados (ML)**: Modelos "black-box" que ignoram a física subjacente.

### Métricas
*   **MAE (Mean Absolute Error)**: Calculado no conjunto de teste (que inclui regiões de extrapolação).
*   **Capacidade de Extrapolação**: A principal métrica qualitativa.
    *   FEM e PINN (se bem configurada) devem extrapolar bem pois respeitam a física globalmente (ou localmente com generalização).
    *   ML Clássico tende a falhar fora da região de treino.
