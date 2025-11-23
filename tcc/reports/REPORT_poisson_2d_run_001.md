# Relatório de Execução: poisson_2d - run_001

**Data do Relatório**: 2025-11-23 04:07:27
**Última Execução**: 2025-11-23T03:58:37.573371

## 1. Configuração do Experimento

| Parâmetro | Valor |
|---|---|
| problem | poisson_2d |
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
| **PINN** | 0.121930 | 🏆 Melhor |
| FEM | 0.171517 | +0.049587 |
| XGB | 0.254084 | +0.132154 |
| RF | 0.255480 | +0.133550 |
| KNN | 0.257639 | +0.135709 |

### Análise Automática
> ✅ **Sucesso**: A PINN superou o Baseline Numérico (FEM) com um erro **28.9% menor**.
## 3. Visualizações

### Comparação Espacial
![Comparação Espacial](../checkpoints/poisson_2d/run_001/comparison.png)

