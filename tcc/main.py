import os
import json
import torch
import numpy as np
import matplotlib.pyplot as plt
import shutil

from config import CONFIG
from problems import get_problem
from models.pinn import train_pinn
from models.fem import PoissonFEM
from models.ml_models import train_ml_models
from utils.plots import plot_comparison
from utils.checkpoint import CheckpointManager

def main():
    print("="*50)
    print(f"INICIANDO EXPERIMENTO: {CONFIG['problem']}")
    print("="*50)

    # 1. Configurar Dispositivo
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    # 2. Carregar Problema
    problem = get_problem(CONFIG)
    
    # 3. Gerenciador de Checkpoints
    ckpt_manager = CheckpointManager()
    run_dir = ckpt_manager.create_run_dir(CONFIG)
    print(f"Diretório de saída: {run_dir}")

    # 4. Treinar PINN
    print("\n--- TREINANDO PINN ---")
    model_pinn = train_pinn(problem, CONFIG)
    
    # 5. Resolver FEM (Ground Truth ou Comparação)
    print("\n--- RESOLVENDO FEM ---")
    fem_solver = None
    u_fem = None
    
    if problem["kind"] == "electrostatic" and problem.get("use_mesh"):
        from solver import ElectrostaticSolver
        fem_data = problem["fem_data"]
        fem_solver = ElectrostaticSolver(
            fem_data["nodes"],
            fem_data["nodeTags"],
            fem_data["triElements"],
            fem_data["elements"],
            fem_data["boundaryConditions"]
        )
        fem_solver.assemble_global_matrix_and_vector()
        fem_solver.apply_boundary_conditions()
        fem_solver.solve()
        u_fem = fem_solver.get_potential()
        print("FEM resolvido com sucesso.")
    elif problem["kind"] == "poisson_2d":
        # Para Poisson analítico, usamos FEM clássico simples se implementado
        # Mas aqui o foco é comparar com analítico u_true
        pass

    # 6. Treinar Modelos ML Clássicos (RF, XGB)
    print("\n--- TREINANDO ML CLÁSSICO ---")
    # Gerar dados de treino/teste compatíveis
    from utils.data import generate_data_for_ml
    X_train, y_train, X_test, y_test = generate_data_for_ml(problem, CONFIG)
    
    ml_metrics, ml_preds = train_ml_models(X_train, y_train, X_test, y_test)
    
    # 7. Avaliar PINN no Test Set
    print("\n--- AVALIAÇÃO FINAL ---")
    # Previsão PINN
    y_pred_pinn = model_pinn.predict(X_test)
    
    # Métricas PINN
    mae_pinn = np.mean(np.abs(y_pred_pinn - y_test))
    
    metrics = {
        "PINN": mae_pinn,
        **ml_metrics
    }
    
    print("\nRESULTADOS (MAE):")
    for k, v in metrics.items():
        print(f"{k}: {v:.6f}")
        
    # 8. Plotar Comparação
    print("\n--- GERANDO GRÁFICOS ---")
    output_plot = os.path.join(run_dir, "comparison.png")
    
    # Ajustar dados para plotagem
    # Se for mesh, precisamos de lógica específica ou usar o visualizer.py
    # O plot_comparison atual é genérico para scatter/line
    if CONFIG.get("use_mesh"):
        # Para mesh, o visualizer.py é melhor, mas vamos gerar um scatter simples aqui
        plt.figure(figsize=(10, 5))
        plt.subplot(1, 2, 1)
        plt.scatter(X_test[:, 0], X_test[:, 1], c=y_pred_pinn.ravel(), cmap='viridis', s=1)
        plt.title("PINN Prediction")
        plt.colorbar()
        
        plt.subplot(1, 2, 2)
        plt.scatter(X_test[:, 0], X_test[:, 1], c=np.abs(y_pred_pinn - y_test).ravel(), cmap='hot', s=1)
        plt.title("Absolute Error")
        plt.colorbar()
        plt.savefig(output_plot)
    else:
        plot_comparison(X_test, y_test, y_pred_pinn, ml_preds, output_plot)
    
    print(f"✓ Gráfico salvo em: {output_plot}")

    # Salvar métricas
    metrics_path = os.path.join(run_dir, "metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=4)
    print(f"✓ Métricas salvas em: {metrics_path}")
    
    # --- COPIAR PARA RESULTS/LATEST ---
    latest_dir = "results/latest"
    os.makedirs(latest_dir, exist_ok=True)
    
    try:
        shutil.copy(output_plot, os.path.join(latest_dir, "comparison.png"))
        shutil.copy(metrics_path, os.path.join(latest_dir, "metrics.json"))
        print(f"✓ Resultados copiados para: {latest_dir}")
    except Exception as e:
        print(f"⚠ Erro ao copiar para latest: {e}")

    print("="*50)
    print("FIM DO TREINAMENTO")
    print("="*50)

if __name__ == "__main__":
    main()
