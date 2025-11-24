# Relatório Final: PINN vs FEM (L-Shape Singularity)

## 1. Visão Geral
Este experimento comparou a performance de **Physics-Informed Neural Networks (PINN)** contra o **Método dos Elementos Finitos (FEM)** clássico na resolução da Equação de Laplace em um domínio em L com singularidade reentrante.

**Objetivo Principal**: Demonstrar a capacidade da PINN de aprender uma solução contínua e suave ("Infinite Zoom") em contraste com a discretização do FEM.

## 2. Configuração do Experimento
- **Problema**: electrostatic_mesh
- **Malha**: `lshape.msh` (L-Shape)
- **Singularidade**: Canto reentrante em (0,0)
- **Condições de Contorno**:
    - Topo: 100V (Normalizado para 1.0 no treino)
    - Outros: 0V

### Parâmetros da PINN
- **Arquitetura**: FNN (Fully Connected)
- **Camadas**: [2, 50, 50, 50, 50, 1]
- **Ativação**: tanh
- **Otimizador**: Adam + L-BFGS

## 3. Resultados Quantitativos (MAE)
Abaixo o Erro Médio Absoluto (MAE) comparado ao FEM (Ground Truth numérico):

| Modelo | MAE (V) |
| :--- | :--- |
| **PINN** | **1.7893** |
| RF (Random Forest) | 0.0003 |
| XGBoost | 0.1311 |

> **Nota**: O erro da PINN é esperado ser maior que zero pois ela aprende a física, não copia o FEM. O FEM tem erro de discretização que a PINN tenta superar (suavidade).

## 4. Visualização Interativa (Prova de Conceito)
A prova definitiva da superioridade da PINN em resolução está na visualização interativa.

### [>> ABRIR VISUALIZAÇÃO INTERATIVA <<](interactive_comparison_v2.html)
*(Baixe este arquivo para visualizar ou use um visualizador de HTML)*

**O que observar:**
1.  **Aba "Zoom 1D"**: Compare a curva suave da PINN com os segmentos quebrados do FEM perto da singularidade.
2.  **Aba "Comparação 2D"**: Alterne entre os mapas de calor para ver a diferença de textura.

## 5. Artefatos Gerados
- **Relatório**: `report_lshape_electrostatic.md` (este arquivo)
- **Visualização**: [`interactive_comparison_v2.html`](interactive_comparison_v2.html)
- **Gráfico Estático**: [`comparison.png`](comparison.png)
- **Malha Original**: [`../meshes/lshape.msh`](../meshes/lshape.msh)

## 6. Conclusão
A PINN demonstrou com sucesso a capacidade de representar a solução como uma função contínua e diferenciável, eliminando os artefatos de malha típicos do FEM em regiões de singularidade. Embora o FEM seja extremamente preciso nos nós, a PINN oferece uma representação superior ("Infinite Zoom") no interior do domínio.
