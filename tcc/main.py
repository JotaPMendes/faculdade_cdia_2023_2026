import os
import sys
import argparse
import json
import time
import numpy as np
import tensorflow as tf
from datetime import datetime

# Configuração de logging e seeds
import random
random.seed(42)
np.random.seed(42)
tf.random.set_seed(42)

# Adicionar diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import load_config
from problems import get_problem
from models.pinn import PINN
from models.ml_models import train_ml_models
from solver import ElectrostaticSolver, MagnetostaticSolver, MagnetodynamicSolver
from utils.mesh_loader import load_mesh_data
from utils.data import generate_data_for_ml

def main():
    # 1. Parse Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=str, required=True, help="Diretório para salvar resultados")
    args = parser.parse_args()
    
    run_dir = args.run_dir
    os.makedirs(run_dir, exist_ok=True)
    
    print("="*50, flush=True)
    print(f"INICIANDO EXPERIMENTO", flush=True)
    print(f"Diretório: {run_dir}", flush=True)
    print("="*50, flush=True)

    # 2. Carregar Configuração
    # Tenta carregar do config.json na raiz, se não usa defaults
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    CONFIG = load_config(config_path)
    
    # Salvar config usada
    with open(os.path.join(run_dir, "config.json"), "w") as f:
        json.dump(CONFIG, f, indent=4)

    # 3. Preparar Problema
    problem = get_problem(CONFIG)
    
    # Se for problema de malha, carregar malha
    fem_solver = None
    u_fem = None
    
    if CONFIG.get("use_mesh"):
        print(f"Carregando malha: {CONFIG['mesh_file']}", flush=True)
        try:
            nodes, nodeTags, triElements, elements, boundaryConditions = load_mesh_data(CONFIG["mesh_file"])
            
            # Atualizar boundary conditions do config se existirem
            if "boundary_conditions" in CONFIG:
                for key, val in CONFIG["boundary_conditions"].items():
                    if key in boundaryConditions:
                        boundaryConditions[key]["potential"] = val
            
            # Criar Solver FEM apropriado
            if CONFIG["problem"] == "electrostatic_mesh":
                fem_solver = ElectrostaticSolver(nodes, nodeTags, triElements, elements, boundaryConditions)
            # Adicionar outros solvers aqui se necessário
            
            if fem_solver:
                print("--- RESOLVENDO FEM ---", flush=True)
                fem_solver.apply_boundary_conditions()
                fem_solver.assemble_global_matrix_and_vector()
                fem_solver.solve()
                fem_solver.calculate_electric_field() # ou magnetic
                u_fem = fem_solver.get_potential()
                print("FEM resolvido com sucesso.", flush=True)
                
                # Atualizar limites do treino baseados na malha
                x_min, y_min = np.min(nodes[:, :2], axis=0)
                x_max, y_max = np.max(nodes[:, :2], axis=0)
                CONFIG["train_box"] = [x_min, y_min, x_max, y_max]
                print(f"✓ Malha carregada: Bounds [{x_min:.2f}, {x_max:.2f}] x [{y_min:.2f}, {y_max:.2f}]", flush=True)
                
        except Exception as e:
            print(f"Erro ao carregar/resolver malha: {e}", flush=True)
            # Não abortar, tentar rodar PINN sem FEM se possível (mas data generation pode falhar)

    # 4. Treinar PINN
    print("\n--- TREINANDO PINN ---", flush=True)
    pinn = PINN(CONFIG, problem)
    
    start_time = time.time()
    history = pinn.train()
    end_time = time.time()
    
    print(f"'train' took {end_time - start_time:.4f} s", flush=True)
    
    # Salvar modelo PINN
    pinn.model.save(os.path.join(run_dir, "pinn_model.h5"))
    
    # Salvar histórico
    history_data = {}
    if history is not None:
        if isinstance(history, tuple):
            # Try to find the LossHistory object in the tuple
            for item in history:
                if hasattr(item, 'history'):
                    history_data = item.history
                    break
        elif hasattr(history, 'history'):
            history_data = history.history
    
    with open(os.path.join(run_dir, "history.json"), "w") as f:
        json.dump(history_data, f, indent=4)

    # 5. Avaliar PINN
    # Gerar pontos de teste
    if CONFIG.get("use_mesh") and fem_solver:
        # Testar nos nós da malha
        X_eval = fem_solver.nodes[:, :2]
        y_true = u_fem
    else:
        # Testar em grid regular
        x = np.linspace(0, CONFIG["Lx"], 100)
        y = np.linspace(0, CONFIG["Ly"], 100)
        X, Y = np.meshgrid(x, y)
        X_eval = np.stack([X.flatten(), Y.flatten()], axis=1)
        if problem.get("u_true"):
            y_true = problem["u_true"](X_eval)
        else:
            y_true = None

    y_pred_pinn = pinn.predict(X_eval)
    
    # Métricas PINN
    final_loss = 0.0
    if 'loss' in history_data and len(history_data['loss']) > 0:
        final_loss = history_data['loss'][-1]

    metrics = {
        "pinn_time": end_time - start_time,
        "pinn_final_loss": final_loss
    }
    
    if y_true is not None:
        mse = np.mean((y_true - y_pred_pinn.flatten())**2)
        metrics["pinn_mse"] = float(mse)
        print(f"PINN MSE: {mse:.2e}", flush=True)

    # 6. Treinar Modelos ML Clássicos (RF, XGB)
    print("\n--- TREINANDO ML CLÁSSICO ---", flush=True)
    
    # Preparar modelo FEM para servir como Ground Truth se necessário
    model_fem_wrapper = None
    if u_fem is not None and fem_solver is not None:
        try:
            from scipy.interpolate import LinearNDInterpolator
            # fem_solver.nodes é (N, 3), pegamos x,y
            # u_fem é (N,)
            print("Criando interpolador FEM para gerar dados de treino ML...", flush=True)
            # Precisamos garantir que nodes e u_fem estão no formato correto
            nodes_xy = fem_solver.nodes[:, :2]
            interp = LinearNDInterpolator(nodes_xy, u_fem, fill_value=0.0)
            
            class FemWrapper:
                def predict(self, x):
                    return interp(x)
            
            model_fem_wrapper = FemWrapper()
        except Exception as e:
            print(f"Erro ao criar interpolador FEM: {e}", flush=True)
    else:
        print("⚠️ u_fem ou fem_solver é None. ML Clássico pode falhar se não houver solução analítica.", flush=True)

    # Gerar dados de treino/teste compatíveis
    X_train, y_train, X_test, y_test = generate_data_for_ml(problem, CONFIG, model_fem=model_fem_wrapper)
    
    if len(X_train) > 0:
        ml_metrics, ml_preds = train_ml_models(X_train, y_train, X_test, y_test)
        metrics.update(ml_metrics)
    else:
        print("⚠️ Sem dados de treino para ML. Pulando...", flush=True)
    
    # 7. Salvar Métricas Finais
    with open(os.path.join(run_dir, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=4)
    
    # 8. Salvar Resumo do Modelo
    model_summary = {
        "type": "PINN",
        "framework": "DeepXDE",
        "config": CONFIG.get("pinn_config", {}),
        "layers": CONFIG.get("pinn_config", {}).get("layers", "Unknown"),
        "activation": CONFIG.get("pinn_config", {}).get("activation", "Unknown")
    }
    with open(os.path.join(run_dir, "model_summary.json"), "w") as f:
        json.dump(model_summary, f, indent=4)

    # 9. Gerar Visualização Interativa
    try:
        from utils.visualizer import generate_interactive_plot
        generate_interactive_plot(run_dir, config=CONFIG, pinn_instance=pinn)
    except Exception as e:
        print(f"Erro ao gerar visualização: {e}", flush=True)
        import traceback
        traceback.print_exc()
        
    print("\n--- EXPERIMENTO CONCLUÍDO ---", flush=True)

if __name__ == "__main__":
    main()
