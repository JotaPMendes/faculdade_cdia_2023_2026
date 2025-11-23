# Relatório de Execução: heat_1d - run_001

**Data do Relatório**: 2025-11-23 04:11:02
**Última Execução**: 2025-11-22T18:13:24.635075

## 1. Configuração do Experimento

| Parâmetro | Valor |
|---|---|
| problem | heat_1d |
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
| **PINN** | 0.010363 | 🏆 Melhor |
| XGB | 0.087316 | +0.076952 |
| KNN | 0.089458 | +0.079094 |
| RF | 0.090392 | +0.080028 |

## 3. Visualizações

### Extrapolação Temporal
![Extrapolação Temporal](../checkpoints/heat_1d/run_001/extrapolation.png)

