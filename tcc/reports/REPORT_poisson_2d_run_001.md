# Relatório de Execução: poisson_2d - run_001

**Data do Relatório**: 2025-11-23 22:00:57
**Última Execução**: 2025-11-23T21:56:25.941552

## 1. Configuração do Experimento

| Parâmetro | Valor |
|---|---|
| problem | poisson_2d |
| mesh_file | domain.msh |
| alpha | 0.1 |
| c | 1.0 |
| Lx | 4.0 |
| T_train | 8.0 |
| T_eval | 16.0 |
| N_data | 5000 |
| x0_list | [0.2, 0.4, 0.6, 0.8] |
| Nx_train | 60 |
| Ny_train | 60 |
| train_box | [0.0, 0.0, 0.6, 1.0] |

## 2. Métricas de Desempenho (MAE)

| Modelo | MAE (Erro Médio Absoluto) | Diferença vs Melhor |
|---|---|---|
| **PINN** | 0.427518 | 🏆 Melhor |
| SVR | 0.450854 | +0.023336 |
| MLP | 0.528766 | +0.101248 |
| XGB | 0.685719 | +0.258201 |
| RF | 0.687070 | +0.259552 |
| KNN | 0.694864 | +0.267346 |
| FEM | 3.819519 | +3.392001 |

### Análise Automática
> ✅ **Sucesso**: A PINN superou o Baseline Numérico (FEM) com um erro **88.8% menor**.
## 3. Visualizações

### Comparação Espacial
![Comparação Espacial](../checkpoints/poisson_2d/run_001/comparison.png)

