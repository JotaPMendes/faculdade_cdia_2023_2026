import matplotlib.pyplot as plt
import numpy as np

def plot_results(problem, model_pinn, model_fem, regressors, results_metrics, cfg):
    """
    Função principal de plotagem. Detecta o tipo de problema e chama
    o visualizador específico.
    """
    if cfg["problem"] == "poisson_2d":
        _plot_spatial_comparison(problem, model_pinn, model_fem, regressors, results_metrics, cfg)
    else:
        _plot_temporal_extrapolation(problem, model_pinn, regressors, results_metrics, cfg)

def _plot_spatial_comparison(problem, model_pinn, model_fem, regressors, metrics, cfg):
    """
    Gera mapas de contorno (Contour Plots) para o Poisson 2D.
    Destaque: Desenha uma caixa vermelha mostrando a área de treino.
    """
    # 1. Criação do Grid de Visualização (100x100)
    gx = np.linspace(0, 1, 100)
    gy = np.linspace(0, 1, 100)
    GX, GY = np.meshgrid(gx, gy)
    Grid = np.stack([GX.ravel(), GY.ravel()], axis=1)

    # 2. Previsões
    # Ground Truth
    U_true = problem["u_true"](Grid).reshape(100, 100)
    
    # PINN
    U_pinn = model_pinn.predict(Grid).reshape(100, 100)
    
    # FEM (se disponível)
    U_fem = None
    if model_fem:
        U_fem = model_fem.predict(Grid).reshape(100, 100)
    
    # Escolher o melhor ML Clássico (baseado na menor métrica MAE passada)
    # Exclui 'PINN' e 'FEM' da busca para achar o melhor regressor
    best_ml_name = min(
        [k for k in metrics.keys() if k not in ["PINN", "FEM"]], 
        key=lambda k: metrics[k]
    )
    # Encontra o objeto do modelo correspondente na lista
    best_ml_model = next(model for name, model in regressors if name == best_ml_name)
    U_ml = best_ml_model.predict(Grid).reshape(100, 100)

    # 3. Plotagem
    # Layout: 1x4 (Real, FEM, PINN, ML)
    fig, ax = plt.subplots(1, 4, figsize=(20, 5), constrained_layout=True)
    
    # Limites da caixa de treino para desenhar
    bx0, by0, bx1, by1 = cfg["train_box"]
    box_x = [bx0, bx1, bx1, bx0, bx0]
    box_y = [by0, by0, by1, by1, by0]

    # Helper para plotar
    def plot_subplot(axis, data, title, show_box=True):
        # Usa vmin/vmax fixos baseados no Real para manter a escala de cores igual
        pcm = axis.contourf(GX, GY, data, levels=50, cmap="viridis", 
                            vmin=U_true.min(), vmax=U_true.max())
        axis.set_title(title, fontsize=11)
        axis.set_xlabel("x")
        axis.set_ylabel("y")
        if show_box:
            axis.plot(box_x, box_y, 'r--', lw=2.5, label="Área de Treino")
            if axis == ax[0]: # Legenda só no primeiro para não poluir
                axis.legend(loc="upper right", framealpha=0.9)
        return pcm

    # Plot A: Real
    pcm = plot_subplot(ax[0], U_true, "Solução Exata (Física)")
    fig.colorbar(pcm, ax=ax[0], shrink=0.6)

    # Plot B: FEM
    if U_fem is not None:
        fem_mae = metrics.get("FEM", 0.0)
        plot_subplot(ax[1], U_fem, f"FEM (Numérico)\nMAE: {fem_mae:.2e}")
        fig.colorbar(pcm, ax=ax[1], shrink=0.6)
    else:
        ax[1].text(0.5, 0.5, "FEM N/A", ha='center')

    # Plot C: PINN
    pinn_mae = metrics.get("PINN", 0.0)
    plot_subplot(ax[2], U_pinn, f"PINN (DeepXDE)\nMAE Extrapolação: {pinn_mae:.2e}")
    fig.colorbar(pcm, ax=ax[2], shrink=0.6)

    # Plot D: Melhor ML
    ml_mae = metrics.get(best_ml_name, 0.0)
    plot_subplot(ax[3], U_ml, f"Melhor ML: {best_ml_name}\nMAE Extrapolação: {ml_mae:.2e}")
    fig.colorbar(pcm, ax=ax[3], shrink=0.6)

    plt.suptitle(f"Comparação de Generalização Espacial - {cfg['problem']}", fontsize=16)
    plt.show()

def _plot_temporal_extrapolation(problem, model_pinn, regressors, metrics, cfg):
    """
    Gera curvas 1D (Heat/Wave) mostrando a evolução no tempo.
    Destaque: Linha vertical separando Treino (passado) vs Avaliação (futuro).
    """
    # 1. Configuração do tempo para plot
    t_full = np.linspace(0, cfg["T_eval"], 300)
    
    # Escolhemos um ponto espacial x0 para "sondar" (Probe)
    # Pega o ponto mais central da lista de x0 configurada
    x_probe = cfg["x0_list"][len(cfg["x0_list"])//2]
    
    # Monta a matriz de entrada [x, t] constante em x, variando em t
    X_probe = np.zeros((len(t_full), 2))
    X_probe[:, 0] = x_probe
    X_probe[:, 1] = t_full

    # 2. Previsões
    y_true = problem["u_true"](X_probe).ravel()
    y_pinn = model_pinn.predict(X_probe).ravel()

    # 3. Plotagem
    plt.figure(figsize=(10, 6))
    
    # Fundo para diferenciar as zonas
    plt.axvspan(0, cfg["T_train"], color='green', alpha=0.05, label="Zona de Treino")
    plt.axvspan(cfg["T_train"], cfg["T_eval"], color='red', alpha=0.05, label="Zona de Extrapolação")
    
    # Curvas
    plt.plot(t_full, y_true, 'k-', lw=2.5, label="Solução Exata")
    plt.plot(t_full, y_pinn, 'r--', lw=2, label=f"PINN (MAE={metrics.get('PINN',0):.1e})")
    
    # Plotar todos os regressores (linhas finas)
    colors = plt.cm.tab10(np.linspace(0, 1, len(regressors)))
    for i, (name, model) in enumerate(regressors):
        y_ml = model.predict(X_probe).ravel()
        plt.plot(t_full, y_ml, linestyle=':', lw=1.5, color=colors[i], 
                 label=f"{name} (MAE={metrics.get(name,0):.1e})")

    # Decorações
    plt.axvline(cfg["T_train"], color="gray", linestyle="-", lw=1)
    plt.title(f"Capacidade de Extrapolação Temporal (x={x_probe}) - {cfg['problem']}", fontsize=14)
    plt.xlabel("Tempo (t)", fontsize=12)
    plt.ylabel(f"u(x={x_probe}, t)", fontsize=12)
    plt.legend(loc="upper left", bbox_to_anchor=(1, 1)) # Legenda fora do gráfico
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.show()