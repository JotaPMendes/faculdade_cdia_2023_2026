import matplotlib.pyplot as plt
import numpy as np

def plot_results(problem, model_pinn, model_fem, regressors, results_metrics, cfg, save_dir=None):
    """
    Função principal de plotagem. Detecta o tipo de problema e chama
    o visualizador específico.
    """
    # Decisão de plotagem baseada no tipo de problema e flag de malha
    use_mesh = problem.get("use_mesh", False)
    
    if use_mesh or cfg["problem"] == "poisson_2d":
        _plot_spatial_comparison(problem, model_pinn, model_fem, regressors, results_metrics, cfg, save_dir)
    else:
        _plot_temporal_extrapolation(problem, model_pinn, regressors, results_metrics, cfg, save_dir)

def _plot_spatial_comparison(problem, model_pinn, model_fem, regressors, metrics, cfg, save_dir=None):
    """
    Gera mapas de contorno (Contour Plots) para o Poisson 2D e Eletrostática.
    Linha 1: Predições (Real, FEM, PINN, ML)
    Linha 2: Erros Absolutos (|Pred - Real|)
    """
    # 1. Criação do Grid de Visualização
    Lx = cfg.get("Lx", 1.0)
    Ly = cfg.get("Ly", 1.0) # Agora usa Ly do config também
    
    gx = np.linspace(0, Lx, 100)
    gy = np.linspace(0, Ly, 100)
    GX, GY = np.meshgrid(gx, gy)
    Grid = np.stack([GX.ravel(), GY.ravel()], axis=1)

    # 2. Previsões e Referência
    # Ground Truth
    if problem.get("u_true") is not None:
        U_true = problem["u_true"](Grid).reshape(100, 100)
        title_true = "Solução Exata (Física)"
    elif model_fem is not None:
        U_true = model_fem.predict(Grid).reshape(100, 100)
        title_true = "Referência (FEM)"
    else:
        U_true = np.zeros((100, 100))
        title_true = "Referência N/A"
    
    # PINN
    U_pinn = model_pinn.predict(Grid).reshape(100, 100)
    
    # FEM (se disponível e não usado como Truth)
    U_fem = None
    if model_fem:
        U_fem = model_fem.predict(Grid).reshape(100, 100)
    
    # Melhor ML
    ml_candidates = [k for k in metrics.keys() if k not in ["PINN", "FEM"]]
    if ml_candidates:
        best_ml_name = min(ml_candidates, key=lambda k: metrics[k])
        best_ml_model = next(model for name, model in regressors if name == best_ml_name)
        U_ml = best_ml_model.predict(Grid).reshape(100, 100)
    else:
        best_ml_name = "N/A"
        U_ml = np.zeros((100, 100))

    # 3. Plotagem
    # Layout: 2x4 (Predições em cima, Erros embaixo)
    fig, ax = plt.subplots(2, 4, figsize=(20, 10), constrained_layout=True)
    
    # Limites da caixa de treino
    bx0, by0, bx1, by1 = cfg["train_box"]
    box_x = [bx0, bx1, bx1, bx0, bx0]
    box_y = [by0, by0, by1, by1, by0]

    # Helper para plotar predição
    def plot_pred(axis, data, title, show_box=True):
        vmin = U_true.min() if U_true.any() else data.min()
        vmax = U_true.max() if U_true.any() else data.max()
        pcm = axis.contourf(GX, GY, data, levels=50, cmap="viridis", vmin=vmin, vmax=vmax)
        axis.set_title(title, fontsize=11)
        axis.set_xlabel("x")
        axis.set_ylabel("y")
        if show_box:
            axis.plot(box_x, box_y, 'r--', lw=2.5, label="Área de Treino")
            if axis == ax[0,0]: axis.legend(loc="upper right", framealpha=0.9)
        return pcm

    # Helper para plotar erro
    def plot_error(axis, data, ref, title):
        error = np.abs(data - ref)
        # Usar escala comum para erros? Ou individual? Individual destaca melhor onde está o erro.
        pcm = axis.contourf(GX, GY, error, levels=50, cmap="inferno")
        axis.set_title(title, fontsize=11)
        axis.set_xlabel("x")
        axis.set_ylabel("y")
        return pcm

    # --- LINHA 1: PREDIÇÕES ---
    
    # A: Real/Referência
    pcm1 = plot_pred(ax[0,0], U_true, title_true)
    fig.colorbar(pcm1, ax=ax[0,0], shrink=0.6)
    
    # B: FEM
    if U_fem is not None:
        fem_mae = metrics.get("FEM", 0.0)
        plot_pred(ax[0,1], U_fem, f"FEM (Numérico)\nMAE: {fem_mae:.2e}")
        fig.colorbar(pcm1, ax=ax[0,1], shrink=0.6)
    else:
        ax[0,1].text(0.5, 0.5, "FEM N/A", ha='center')

    # C: PINN
    pinn_mae = metrics.get("PINN", 0.0)
    plot_pred(ax[0,2], U_pinn, f"PINN (DeepXDE)\nMAE: {pinn_mae:.2e}")
    fig.colorbar(pcm1, ax=ax[0,2], shrink=0.6)

    # D: ML
    ml_mae = metrics.get(best_ml_name, 0.0)
    plot_pred(ax[0,3], U_ml, f"Melhor ML: {best_ml_name}\nMAE: {ml_mae:.2e}")
    fig.colorbar(pcm1, ax=ax[0,3], shrink=0.6)

    # --- LINHA 2: ERROS ---
    
    # A: Erro Referência (Zero)
    plot_error(ax[1,0], U_true, U_true, "Erro Referência (Zero)")
    
    # B: Erro FEM (Zero se for a referência)
    if U_fem is not None:
        pcm_err = plot_error(ax[1,1], U_fem, U_true, "Erro Absoluto FEM")
        fig.colorbar(pcm_err, ax=ax[1,1], shrink=0.6)
    else:
        ax[1,1].text(0.5, 0.5, "N/A", ha='center')

    # C: Erro PINN
    pcm_err_pinn = plot_error(ax[1,2], U_pinn, U_true, "Erro Absoluto PINN")
    fig.colorbar(pcm_err_pinn, ax=ax[1,2], shrink=0.6)

    # D: Erro ML
    pcm_err_ml = plot_error(ax[1,3], U_ml, U_true, f"Erro Absoluto {best_ml_name}")
    fig.colorbar(pcm_err_ml, ax=ax[1,3], shrink=0.6)

    plt.suptitle(f"Comparação Espacial e Erros - {cfg['problem']}", fontsize=16)
    
    if save_dir:
        import os
        save_path = os.path.join(save_dir, "comparison.png")
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✓ Gráfico salvo em: {save_path}")
        
    plt.show()

def _plot_temporal_extrapolation(problem, model_pinn, regressors, metrics, cfg, save_dir=None):
    """
    Gera curvas 1D (Heat/Wave) mostrando a evolução no tempo.
    """
    t_full = np.linspace(0, cfg["T_eval"], 300)
    x_probe = cfg["x0_list"][len(cfg["x0_list"])//2]
    
    X_probe = np.zeros((len(t_full), 2))
    X_probe[:, 0] = x_probe
    X_probe[:, 1] = t_full

    if problem.get("u_true") is not None:
        y_true = problem["u_true"](X_probe).ravel()
    else:
        y_true = np.zeros_like(t_full)

    y_pinn = model_pinn.predict(X_probe).ravel()

    plt.figure(figsize=(10, 6))
    plt.axvspan(0, cfg["T_train"], color='green', alpha=0.05, label="Zona de Treino")
    plt.axvspan(cfg["T_train"], cfg["T_eval"], color='red', alpha=0.05, label="Zona de Extrapolação")
    
    if problem.get("u_true") is not None:
        plt.plot(t_full, y_true, 'k-', lw=2.5, label="Solução Exata")
    
    plt.plot(t_full, y_pinn, 'r--', lw=2, label=f"PINN (MAE={metrics.get('PINN',0):.1e})")
    
    colors = plt.cm.tab10(np.linspace(0, 1, len(regressors)))
    for i, (name, model) in enumerate(regressors):
        y_ml = model.predict(X_probe).ravel()
        plt.plot(t_full, y_ml, linestyle=':', lw=1.5, color=colors[i], 
                 label=f"{name} (MAE={metrics.get(name,0):.1e})")

    plt.axvline(cfg["T_train"], color="gray", linestyle="-", lw=1)
    plt.title(f"Capacidade de Extrapolação Temporal (x={x_probe}) - {cfg['problem']}", fontsize=14)
    plt.xlabel("Tempo (t)", fontsize=12)
    plt.ylabel(f"u(x={x_probe}, t)", fontsize=12)
    plt.legend(loc="upper left", bbox_to_anchor=(1, 1))
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    
    if save_dir:
        import os
        save_path = os.path.join(save_dir, "extrapolation.png")
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✓ Gráfico salvo em: {save_path}")

    plt.show()