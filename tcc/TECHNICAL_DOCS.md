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

#### 1.2.1. Otimizações Implementadas

Com base em pesquisa no repositório oficial do DeepXDE, implementamos as seguintes otimizações para o problema de Poisson 2D:

**A. Ativação `tanh` (Revertido)**
*   **Motivação**: Inicialmente testamos `sin`, mas combinada com MsFFN gerou instabilidade inicial. `tanh` provou ser mais robusta para este problema específico, mantendo a capacidade de aprendizado sem explodir gradientes.
*   **Implementação**: `net = dde.nn.MsFFN([2] + [64]*5 + [1], "tanh", ...)`

**B. Sobol Sampling**
*   **Motivação**: Sampling pseudorandom pode criar clusters e deixar regiões vazias. Sobol sequences (quasi-random) garantem cobertura mais uniforme do domínio, reduzindo pontos redundantes.
*   **Referência**: DeepXDE suporta nativamente Sobol, Halton, e Hammersley sequences para melhor distribuição espacial.
*   **Implementação**: `train_distribution="Sobol"` no `dde.data.PDE`
*   **Trade-off**: Warnings sobre potências de 2 são esperados, mas não afetam significativamente a qualidade.

**C. Escalas Fourier Ajustadas**
*   **Motivação**: Testamos `[1, 5, 10, 50]`, mas a escala `50` causou explosão da derivada segunda ($\nabla^2 u \approx \sigma^2$), elevando a loss inicial para $10^9$.
*   **Ajuste**: Reduzimos para `[1, 5, 10]`, o que estabilizou a inicialização ($10^6$) mantendo boa capacidade de capturar frequências médias.
*   **Implementação**: `sigmas=[1, 5, 10]`

**D. Rede Mais Profunda**
*   **Motivação**: Aumentar de `[50]*4` para `[64]*5` (4→5 camadas, 50→64 neurônios) aumenta a capacidade da rede sem overhead computacional excessivo.
*   **Referência**: DeepXDE examples para Poisson 2D usam tipicamente 4-6 camadas com 50-100 neurônios.
*   **Implementação**: `[2] + [64]*5 + [1]`

**E. Conjunto de Teste Separado**
*   **Motivação**: Sem `num_test`, DeepXDE reutiliza pontos de treino para validação, resultando em train_loss = test_loss (falso positivo de generalização).
*   **Implementação**: `num_test=2000` (≈16% do treino) para validação independente.
*   **Impacto**: Permite detecção precoce de overfitting via Early Stopping.

**F. Early Stopping**
*   **Motivação**: Evita desperdício de tempo em modelos que estagnaram.
*   **Implementação**: `dde.callbacks.EarlyStopping(min_delta=1e-4, patience=2000)`
*   **Critério**: Para se a loss não melhorar `1e-4` por 2000 iterações consecutivas.

**G. RAR (Residual-based Adaptive Refinement)**
*   **Motivação**: Pontos de colocação fixos podem não capturar regiões de alto erro (ex: bordas ou picos da função). O RAR adiciona dinamicamente pontos onde o resíduo da PDE é maior.
*   **Implementação**: `dde.callbacks.PDEPointResampler(period=1000)`
*   **Funcionamento**: A cada 1000 iterações, avalia o erro em um conjunto denso de candidatos e adiciona os piores pontos ao conjunto de treino.
*   **Impacto**: Melhora a precisão em regiões críticas sem aumentar drasticamente o custo computacional total.

#### 1.2.2. Correção Crítica: Boundary Conditions

**Problema Identificado**: A implementação inicial usava `bc = dde.icbc.DirichletBC(geom, lambda X: 0.0, ...)`, forçando $u=0$ em **toda a borda** do `train_box` $[0, 0.6] \times [0, 1]$.

**Por que isso é errado?**
*   A borda interna em $x=0.6$ **não** faz parte da borda física do problema original $[0,1]^2$.
*   A solução verdadeira em $x=0.6$ é $u(0.6, y) = \sin(0.6\pi)\sin(\pi y) \approx 0.95\sin(\pi y) \neq 0$.
*   Forçar $u=0$ criava um gradiente artificial massivo na interface, impedindo a PINN de aprender corretamente.

**Solução Implementada**:
```python
bc = dde.icbc.DirichletBC(geom, u_true, lambda X, on_b: on_b)
```
*   Agora a BC usa os **valores verdadeiros** da solução analítica na borda.
*   Isso garante continuidade física e permite que a PINN aprenda a física correta dentro do `train_box` e extrapole para fora.

**Impacto**: Esta correção foi **fundamental** para permitir que a PINN competisse com o FEM. Antes da correção, o MAE era >0.5. Depois, caiu para ~0.19.

### 1.3. Machine Learning Clássico
Os modelos de ML (`models/regressors.py`) tratam o problema como uma regressão pura $f(x,y) \to u$.

*   **Dados**: Treinados apenas com pontos amostrados dentro do `train_box`.
*   **Modelos**:
    *   **Random Forest**: Ensemble de árvores de decisão. Bom para capturar não-linearidades, mas péssimo em extrapolação.
    *   **XGBoost**: Boosting de gradiente. Alta performance em interpolação.
    *   **KNN**: Baseado em vizinhança. Simples, mas sofre com a maldição da dimensionalidade e não extrapola bem.

### 1.3.1. Melhorias nos Regressores (Baselines Avançados)
Para uma comparação científica mais justa, adicionamos dois modelos que capturam melhor a natureza contínua das EDPs:

*   **MLP (Multi-layer Perceptron)**:
    *   **Motivação**: Baseline direto para a PINN. Ambas são redes neurais; a diferença é que a MLP usa apenas dados (Data-driven) enquanto a PINN usa Física (Physics-informed).
    *   **Objetivo**: Isolar o ganho de performance vindo da "Física".
*   **SVR (Support Vector Regression)**:
    *   **Motivação**: Excelente capacidade de interpolação para funções suaves em baixa dimensão.

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

## 3. Metodologia de Comparação e Resultados

A comparação é realizada em três níveis:

1.  **Física (Ground Truth)**: Solução analítica exata.
2.  **Numérica (FEM)**: Aproximação tradicional de alta ordem. Serve para validar se a PINN está convergindo para a solução física correta.
3.  **Dados (ML)**: Modelos "black-box" que ignoram a física subjacente.

### Métricas e Resultados (Poisson 2D)
*   **MAE (Mean Absolute Error)**: Calculado no conjunto de teste (que inclui regiões de extrapolação).

**Ranking Final Observado:**
1.  🏆 **SVR**: `0.090` (Excelente interpolação suave)
2.  🥈 **PINN**: `0.124` (Superou o baseline numérico FEM)
3.  🥉 **FEM**: `0.173` (Baseline numérico padrão)
4.  **MLP**: `0.211` (Rede Neural sem física)

**Conclusão**: A PINN superou significativamente a MLP padrão (0.124 vs 0.211), provando que a incorporação da física (PDE Loss) foi crucial para o aprendizado, permitindo que a rede superasse até mesmo o método numérico tradicional (FEM) em precisão neste cenário.
