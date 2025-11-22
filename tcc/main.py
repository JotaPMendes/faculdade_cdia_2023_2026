"""
Script principal para treinar e comparar PINN vs ML Clássico.

Este script:
1. Carrega o problema configurado (Heat, Wave ou Poisson)
2. Treina o modelo PINN
3. Treina modelos de ML Clássico (RF, XGB, KNN)
4. Compara os resultados
5. Gera visualizações
"""

import numpy as np
from sklearn.metrics import mean_absolute_error

from config import CONFIG
from problems import make_problem
from models.pinn import train_pinn
from models.regressors import get_regressors
from models.fem import PoissonFEM
from utils.data import generate_data_for_ml
from utils.plots import plot_results
from utils.checkpoint import CheckpointManager
import json
import os


def main():
    print("=" * 70)
    print("COMPARAÇÃO: PINN vs ML CLÁSSICO")
    print("=" * 70)
    print(f"\nProblema selecionado: {CONFIG['problem']}")
    print(f"Configurações:")
    for key, value in CONFIG.items():
        print(f"  {key}: {value}")
    
    # =============================
    # 1. CRIAR PROBLEMA
    # =============================
    print("\n" + "=" * 70)
    print("ETAPA 1: Criando problema...")
    print("=" * 70)
    problem = make_problem(CONFIG)
    print(f"✓ Problema criado: tipo='{problem['kind']}'")
    print(f"✓ Componentes: data={type(problem['data']).__name__}, net={type(problem['net']).__name__}")
    
    # Instanciar Manager para obter diretório de salvamento
    ckpt_manager = CheckpointManager(max_keep=3)
    ckpt_dir = ckpt_manager.get_run_dir(CONFIG)
    print(f"✓ Diretório de execução: {ckpt_dir}")
    
    # =============================
    # 2. TREINAR PINN
    # =============================
    print("\n" + "=" * 70)
    print("ETAPA 2: Treinando PINN...")
    print("=" * 70)
    model_pinn = train_pinn(problem, CONFIG)
    print("✓ PINN treinado com sucesso!")

    # =============================
    # 2.1. RESOLVER FEM (Reference)
    # =============================
    model_fem = None
    if CONFIG["problem"] == "poisson_2d":
        print("\n" + "=" * 70)
        print("ETAPA 2.1: Resolvendo FEM (Baseline Numérico)...")
        print("=" * 70)
        model_fem = PoissonFEM(problem, Nx=50, Ny=50)
        model_fem.solve()
        print("✓ FEM resolvido com sucesso!")
    
    # =============================
    # 3. GERAR DADOS PARA ML
    # =============================
    print("\n" + "=" * 70)
    print("ETAPA 3: Gerando dados para ML Clássico...")
    print("=" * 70)
    Xtr, ytr, Xte, yte = generate_data_for_ml(problem, CONFIG)
    print(f"✓ Dados de treino: X_train.shape = {Xtr.shape}, y_train.shape = {ytr.shape}")
    print(f"✓ Dados de teste: X_test.shape = {Xte.shape}, y_test.shape = {yte.shape}")
    
    # =============================
    # 4. TREINAR ML CLÁSSICO
    # =============================
    print("\n" + "=" * 70)
    print("ETAPA 4: Treinando modelos de ML Clássico...")
    print("=" * 70)
    regressors = get_regressors()
    trained_models = []
    
    for name, model in regressors:
        print(f"\nTreinando {name}...")
        model.fit(Xtr, ytr.ravel())
        score_train = model.score(Xtr, ytr.ravel())
        score_test = model.score(Xte, yte.ravel())
        print(f"  R² (treino): {score_train:.4f}")
        print(f"  R² (teste):  {score_test:.4f}")
        trained_models.append((name, model))
    
    print("\n✓ Todos os modelos ML treinados!")
    
    # =============================
    # 5. AVALIAR NO CONJUNTO DE TESTE
    # =============================
    print("\n" + "=" * 70)
    print("ETAPA 5: Avaliando modelos no conjunto de teste...")
    print("=" * 70)
    
    results_metrics = {}
    
    # Avaliar PINN
    print("\nAvaliando PINN...")
    y_pred_pinn = model_pinn.predict(Xte)
    mae_pinn = mean_absolute_error(yte, y_pred_pinn)
    results_metrics["PINN"] = mae_pinn
    print(f"  MAE (PINN): {mae_pinn:.6f}")

    # Avaliar FEM
    if model_fem:
        print("\nAvaliando FEM...")
        y_pred_fem = model_fem.predict(Xte)
        mae_fem = mean_absolute_error(yte, y_pred_fem)
        results_metrics["FEM"] = mae_fem
        print(f"  MAE (FEM):  {mae_fem:.6f}")
    
    # Avaliar ML Clássico
    for name, model in trained_models:
        y_pred = model.predict(Xte)
        mae = mean_absolute_error(yte, y_pred)
        results_metrics[name] = mae
        print(f"  MAE ({name}):  {mae:.6f}")
    
    # =============================
    # 6. RESULTADOS FINAIS
    # =============================
    print("\n" + "=" * 70)
    print("RESULTADOS FINAIS - MAE (Mean Absolute Error)")
    print("=" * 70)
    
    # Ordenar por MAE (menor é melhor)
    sorted_results = sorted(results_metrics.items(), key=lambda x: x[1])
    
    print("\nRanking (menor MAE é melhor):")
    for i, (name, mae) in enumerate(sorted_results, 1):
        symbol = "🏆" if i == 1 else "  "
        print(f"{symbol} {i}. {name:10s} - MAE: {mae:.6f}")
    
    best_model = sorted_results[0][0]
    print(f"\n✓ Melhor modelo: {best_model}")
    
    # Salvar métricas em JSON
    metrics_path = os.path.join(ckpt_dir, "metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(results_metrics, f, indent=2)
    print(f"✓ Métricas salvas em: {metrics_path}")
    
    # =============================
    # 7. GERAR VISUALIZAÇÕES
    # =============================
    print("\n" + "=" * 70)
    print("ETAPA 6: Gerando visualizações...")
    print("=" * 70)
    
    try:
        plot_results(problem, model_pinn, model_fem, trained_models, results_metrics, CONFIG, save_dir=ckpt_dir)
        print("✓ Gráficos salvos com sucesso!")
    except Exception as e:
        print(f"⚠ Erro ao gerar gráficos: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("EXECUÇÃO CONCLUÍDA!")
    print("=" * 70)


if __name__ == "__main__":
    main()
