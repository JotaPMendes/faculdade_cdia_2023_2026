import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import meshio
import os
import sys
from scipy.interpolate import griddata
import shutil

# Adicionar raiz ao path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import CONFIG
from problems import get_problem
from models.pinn import PINN
from solver import ElectrostaticSolver, MagnetostaticSolver, MagnetodynamicSolver
from utils.checkpoint import CheckpointManager

def generate_interactive_plot(run_dir=None, config=None, pinn_instance=None):
    print("="*50)
    print("GERADOR DE VISUALIZAÇÃO CIENTÍFICA (PLOTLY)")
    print("="*50)

    # 0. Usar config fornecida ou global
    if config is None:
        config = CONFIG

    # 1. Carregar Configuração e Problema
    problem = get_problem(config)
    
    if run_dir is None:
        ckpt_manager = CheckpointManager()
        run_dir = ckpt_manager.get_run_dir(config)
        print(f"✓ Diretório detectado: {run_dir}")

    # Dispatch based on problem type
    problem_type = config.get("problem", "unknown")
    print(f"✓ Tipo de Problema Detectado: {problem_type}")

    if problem_type in ["heat_1d", "wave_1d"]:
        return plot_1d(run_dir, config, pinn_instance, problem)
    elif problem_type == "poisson_2d":
        return plot_2d(run_dir, config, pinn_instance, problem)
    elif "mesh" in problem_type:
        return plot_mesh(run_dir, config, pinn_instance, problem)
    else:
        print(f"⚠️ Tipo de problema '{problem_type}' não suportado para visualização automática.")
        return

def plot_1d(run_dir, config, pinn_instance, problem):
    print("--- Gerando Visualização 1D (Espaço-Tempo) ---")
    
    # 1. Preparar Grid (X, T)
    Lx = config.get("Lx", 1.0)
    T_train = config.get("T_train", 1.0)
    
    Nx = 100
    Nt = 100
    x = np.linspace(0, Lx, Nx)
    t = np.linspace(0, T_train, Nt)
    X, T = np.meshgrid(x, t)
    X_eval = np.stack([X.flatten(), T.flatten()], axis=1)
    
    # 2. Predição PINN
    if pinn_instance is None:
        pinn = PINN(config, problem)
        pinn.train() # Load weights if available
        pinn_instance = pinn
        
    y_pred = pinn_instance.predict(X_eval).reshape(Nt, Nx)
    
    # 3. Solução Exata (se houver)
    y_true = None
    if problem.get("u_true"):
        y_true = problem["u_true"](X_eval).reshape(Nt, Nx)
        error = np.abs(y_pred - y_true)
        mae = np.mean(error)
        print(f"Métricas: MAE={mae:.2e}")
    
    # 4. Plots
    cols = 2 if y_true is not None else 1
    fig = make_subplots(
        rows=2, cols=cols,
        subplot_titles=("Solução PINN (x,t)", "Solução Exata (x,t)" if y_true is not None else "", "Slices Temporais"),
        specs=[[{}, {}] if cols==2 else [{}], [{"colspan": cols}, None] if cols==2 else [{}]]
    )
    
    # Heatmap PINN
    fig.add_trace(go.Heatmap(
        x=x, y=t, z=y_pred,
        colorscale='Viridis',
        name='PINN',
        colorbar=dict(
            title='u(x,t)', 
            x=0.46 if cols==2 else 1.0, 
            len=0.4, 
            y=0.8,
            thickness=15
        )
    ), row=1, col=1)
    
    if y_true is not None:
        # Heatmap True
        fig.add_trace(go.Heatmap(
            x=x, y=t, z=y_true,
            colorscale='Viridis',
            name='Exata',
            colorbar=dict(
                title='u_true', 
                x=1.0, 
                len=0.4, 
                y=0.8,
                thickness=15
            )
        ), row=1, col=2)
        
    # Slices
    times_to_plot = [0.0, T_train/2, T_train]
    colors = ['cyan', 'orange', 'magenta']
    
    for i, t_val in enumerate(times_to_plot):
        # Find closest index
        idx = (np.abs(t - t_val)).argmin()
        
        fig.add_trace(go.Scatter(
            x=x, y=y_pred[idx, :],
            mode='lines',
            name=f'PINN t={t_val:.2f}',
            line=dict(color=colors[i], dash='solid')
        ), row=2, col=1)
        
        if y_true is not None:
            fig.add_trace(go.Scatter(
                x=x, y=y_true[idx, :],
                mode='lines',
                name=f'Exata t={t_val:.2f}',
                line=dict(color=colors[i], dash='dot')
            ), row=2, col=1)

    fig.update_layout(
        title=f"Análise 1D: {config['problem']}",
        template="plotly_dark",
        height=800,
        xaxis_title="Posição (x)",
        yaxis_title="Tempo (t)"
    )
    
    save_plot(fig, run_dir)

def plot_2d(run_dir, config, pinn_instance, problem):
    print("--- Gerando Visualização 2D (Poisson) ---")
    
    # 1. Grid (X, Y)
    Lx = config.get("Lx", 1.0)
    Ly = config.get("Ly", 1.0)
    
    Nx = 100
    Ny = 100
    x = np.linspace(0, Lx, Nx)
    y = np.linspace(0, Ly, Ny)
    X, Y = np.meshgrid(x, y)
    X_eval = np.stack([X.flatten(), Y.flatten()], axis=1)
    
    # 2. Predição
    if pinn_instance is None:
        pinn = PINN(config, problem)
        pinn.train()
        pinn_instance = pinn
        
    u_pred = pinn_instance.predict(X_eval).reshape(Ny, Nx)
    
    # 3. Exata
    u_true = None
    if problem.get("u_true"):
        u_true = problem["u_true"](X_eval).reshape(Ny, Nx)
        error = np.abs(u_pred - u_true)
    
    # Layout
    fig = make_subplots(
        rows=1, cols=3 if u_true is not None else 1,
        subplot_titles=("PINN", "Exata", "Erro Absoluto") if u_true is not None else ("PINN",)
    )
    
    fig.add_trace(go.Heatmap(z=u_pred, x=x, y=y, colorscale='Viridis', name='PINN'), row=1, col=1)
    
    if u_true is not None:
        fig.add_trace(go.Heatmap(z=u_true, x=x, y=y, colorscale='Viridis', name='Exata'), row=1, col=2)
        fig.add_trace(go.Heatmap(z=error, x=x, y=y, colorscale='Magma', name='Erro'), row=1, col=3)
        
    fig.update_layout(title=f"Análise 2D: {config['problem']}", template="plotly_dark", height=500)
    save_plot(fig, run_dir)

def plot_mesh(run_dir, config, pinn_instance, problem):
    print("--- Gerando Visualização Mesh (FEM vs PINN) ---")
    
    mesh_file = config["mesh_file"]
    mesh = meshio.read(mesh_file)
    points = mesh.points[:, :2]
    triangles = mesh.cells_dict.get("triangle")
    
    if pinn_instance is None:
        pinn = PINN(config, problem)
        pinn.train()
        pinn_instance = pinn
        
    # FEM Solver Selection
    if "fem_data" not in problem:
        print("⚠️ Dados FEM não encontrados no problema. Pulando comparação FEM.")
        return

    fem_data = problem["fem_data"]
    kind = problem.get("kind", "electrostatic")
    
    print(f"Resolvendo FEM ({kind})...")
    
    solver = None
    if kind == "electrostatic":
        solver = ElectrostaticSolver(
            fem_data["nodes"], fem_data["nodeTags"], fem_data["triElements"],
            fem_data["elements"], fem_data["boundaryConditions"]
        )
    elif kind == "magnetostatic":
        solver = MagnetostaticSolver(
            fem_data["nodes"], fem_data["nodeTags"], fem_data["triElements"],
            fem_data["elements"], fem_data["boundaryConditions"]
        )
    elif kind == "magnetodynamic":
        solver = MagnetodynamicSolver(
            fem_data["nodes"], fem_data["nodeTags"], fem_data["triElements"],
            fem_data["elements"], fem_data["boundaryConditions"], fem_data["frequency"]
        )
    
    if solver:
        solver.assemble_global_matrix_and_vector()
        solver.apply_boundary_conditions()
        solver.solve()
        fem_potential = solver.get_potential()
        
        # Handle Complex Numbers for Magnetodynamic
        if np.iscomplexobj(fem_potential):
            fem_potential = np.abs(fem_potential) # Magnitude for visualization
    else:
        print("Solver não instanciado.")
        return

    # 4. Preparar Dados 2D
    scale = problem.get("scaling_factor", 1.0)
    
    # PINN Prediction
    pinn_pred = pinn_instance.predict(points)
    if pinn_pred.shape[1] == 2: # Magnetodynamic (Real, Imag)
        # Magnitude: sqrt(Real^2 + Imag^2)
        U_pinn = np.sqrt(pinn_pred[:,0]**2 + pinn_pred[:,1]**2) * scale
    else:
        U_pinn = pinn_pred.ravel() * scale
        
    U_fem = np.abs(fem_potential) * 1.0 # Ensure magnitude
    U_error = np.abs(U_pinn - U_fem)
    
    # DEBUG STATS
    print(f"DEBUG: U_pinn range: [{U_pinn.min():.2e}, {U_pinn.max():.2e}]")
    print(f"DEBUG: U_fem range: [{U_fem.min():.2e}, {U_fem.max():.2e}]")
    print(f"DEBUG: U_error range: [{U_error.min():.2e}, {U_error.max():.2e}]")
    
    # Métricas Globais
    mae = np.mean(U_error)
    l2 = np.linalg.norm(U_error) / np.linalg.norm(U_fem)
    linf = np.max(U_error)
    
    print(f"Métricas: MAE={mae:.2e}, L2={l2:.2e}, Linf={linf:.2e}")

    # Triângulos para Plotly
    if triangles is None:
        use_mesh_plot = False
    else:
        use_mesh_plot = True
        tri_i = triangles[:, 0]
        tri_j = triangles[:, 1]
        tri_k = triangles[:, 2]

    # 5. Preparar Dados Slice 1D
    slice_cfg = config.get("slice_config", {
        "type": "linear",
        "p_start": [-0.5, -0.5],
        "p_end": [0.0, 0.0],
        "xlabel": "Posição"
    })
    
    p_start = np.array(slice_cfg["p_start"])
    p_end = np.array(slice_cfg["p_end"])
    
    N_slice = 200
    t = np.linspace(0, 1, N_slice)
    slice_points = p_start + np.outer(t, (p_end - p_start))
    
    if slice_cfg.get("type") == "radial":
        slice_x = np.linalg.norm(slice_points, axis=1)
        xlabel = "Raio (m)"
    else:
        slice_x = np.linalg.norm(slice_points - p_start, axis=1)
        xlabel = "Distância (m)"
    
    # Slice Prediction
    slice_pred_pinn = pinn_instance.predict(slice_points)
    if slice_pred_pinn.shape[1] == 2:
        slice_pinn = np.sqrt(slice_pred_pinn[:,0]**2 + slice_pred_pinn[:,1]**2) * scale
    else:
        slice_pinn = slice_pred_pinn.ravel() * scale
        
    slice_fem = griddata(points, U_fem, slice_points, method='linear')
    slice_error = np.abs(slice_pinn - slice_fem)

    # --- PLOTLY LAYOUT ---
    fig = make_subplots(
        rows=2, cols=2,
        column_widths=[0.55, 0.45],
        row_heights=[0.5, 0.5],
        specs=[
            [{"type": "scene", "rowspan": 2}, {"type": "xy"}],
            [None, {"type": "xy"}]
        ],
        subplot_titles=(
            "<b>Malha & Solução (Visualização 3D)</b>", 
            "<b>Slice 1D: Comparação de Potencial</b>", 
            "<b>Slice 1D: Erro Absoluto (|PINN - FEM|)</b>"
        ),
        vertical_spacing=0.15,
        horizontal_spacing=0.1
    )

    # --- 2D MAP TRACES ---
    def create_mesh_trace(values, name, visible, colorscale, cmin=None, cmax=None):
        if use_mesh_plot:
            return go.Mesh3d(
                x=points[:, 0], y=points[:, 1], z=np.zeros_like(points[:, 0]),
                i=tri_i, j=tri_j, k=tri_k,
                intensity=values,
                colorscale=colorscale,
                cmin=cmin, cmax=cmax,
                colorbar=dict(
                    title=dict(text=name, side="right"), 
                    x=0.46, 
                    len=0.8,
                    thickness=15,
                    tickfont=dict(size=12)
                ),
                name=name,
                visible=visible,
                flatshading=False, 
            )
        else:
            return go.Scatter(
                x=points[:, 0], y=points[:, 1],
                mode='markers',
                marker=dict(size=4, color=values, colorscale=colorscale, showscale=True),
                name=name, visible=visible
            )

    v_min, v_max = min(U_fem.min(), U_pinn.min()), max(U_fem.max(), U_pinn.max())
    
    # 1. PINN Map
    fig.add_trace(create_mesh_trace(U_pinn, "V (PINN)", True, 'Viridis', v_min, v_max), row=1, col=1)
    # 2. FEM Map
    fig.add_trace(create_mesh_trace(U_fem, "V (FEM)", False, 'Viridis', v_min, v_max), row=1, col=1)
    # 3. Error Map
    fig.add_trace(create_mesh_trace(U_error, "Erro Abs (V)", False, 'Magma'), row=1, col=1)

    # 4. Slice Line on Map
    fig.add_trace(go.Scatter3d(
        x=slice_points[:, 0], y=slice_points[:, 1], z=np.ones_like(slice_x)*0.01,
        mode='lines',
        line=dict(color='white', width=4, dash='dash'),
        name='Slice Location',
        hoverinfo='skip'
    ), row=1, col=1)

    # --- 1D SLICE TRACES ---
    # 5. PINN Slice
    fig.add_trace(go.Scatter(
        x=slice_x, y=slice_pinn,
        mode='lines',
        name='PINN',
        line=dict(color='#00FFFF', width=3),
    ), row=1, col=2)
    
    # 6. FEM Slice
    fig.add_trace(go.Scatter(
        x=slice_x, y=slice_fem,
        mode='lines+markers',
        name='FEM',
        line=dict(color='#FFA500', width=2, dash='dot'),
        marker=dict(size=5, symbol='circle', maxdisplayed=30)
    ), row=1, col=2)

    # --- 1D ERROR TRACES ---
    # 7. Error Slice
    fig.add_trace(go.Scatter(
        x=slice_x, y=slice_error,
        mode='lines',
        name='Erro Absoluto',
        line=dict(color='#FF4444', width=2),
        fill='tozeroy',
        fillcolor='rgba(255, 68, 68, 0.2)'
    ), row=2, col=2)

    # --- LAYOUT STYLING ---
    fig.update_layout(
        title=dict(
            text=f"<b>Análise Comparativa: {os.path.basename(config['mesh_file'])}</b><br>" + 
                 f"<span style='font-size: 14px; color: gray;'>Métricas Globais: MAE={mae:.2e} | L2={l2:.2e} | Linf={linf:.2e}</span>",
            y=0.97, x=0.5, xanchor='center', yanchor='top',
            font=dict(size=22)
        ),
        template="plotly_dark",
        paper_bgcolor="#1e1e1e",
        plot_bgcolor="#1e1e1e",
        height=850,
        margin=dict(t=100, b=50, l=50, r=50),
        legend=dict(
            x=0.55, 
            y=1.02, 
            orientation="h",
            xanchor="center",
            entrywidth=70  # Force spacing
        ),
        
        scene=dict(
            xaxis=dict(title='X (m)', showgrid=True, zeroline=False),
            yaxis=dict(title='Y (m)', showgrid=True, zeroline=False),
            zaxis=dict(title='', showticklabels=False, range=[-1, 1], showgrid=True),
            camera=dict(
                eye=dict(x=5, y=5, z=5), # Zoom out (was 1.5)
                up=dict(x=0, y=0, z=1)
            ),
            aspectmode='data',
            dragmode='orbit'
        )
    )

    fig.update_xaxes(title_text=xlabel, row=1, col=2)
    fig.update_yaxes(title_text="Potencial", row=1, col=2)
    fig.update_xaxes(title_text=xlabel, row=2, col=2)
    fig.update_yaxes(title_text="Erro Absoluto", row=2, col=2)

    # --- INTERACTIVE BUTTONS ---
    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="down",
                active=0,
                x=0.0, y=1.0,
                bgcolor="#2d2d2d",
                bordercolor="#444",
                font=dict(size=12),
                buttons=list([
                    dict(label="PINN",
                         method="update",
                         args=[{"visible": [True, False, False, True, True, True, True]},
                               {"title.text": f"<b>Análise Comparativa: {os.path.basename(config['mesh_file'])}</b><br>Visualizando: PINN"}]),
                    dict(label="FEM",
                         method="update",
                         args=[{"visible": [False, True, False, True, True, True, True]},
                               {"title.text": f"<b>Análise Comparativa: {os.path.basename(config['mesh_file'])}</b><br>Visualizando: FEM"}]),
                    dict(label="ERRO",
                         method="update",
                         args=[{"visible": [False, False, True, True, True, True, True]},
                               {"title.text": f"<b>Análise Comparativa: {os.path.basename(config['mesh_file'])}</b><br>Visualizando: Erro Absoluto"}])
                ]),
            )
        ]
    )
    
    save_plot(fig, run_dir)

def save_plot(fig, run_dir):
    output_file = os.path.join(run_dir, "interactive_comparison_v2.html")
    fig.write_html(output_file)
    print(f"✓ Visualização salva em: {output_file}")
    
    latest_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", "latest")
    os.makedirs(latest_dir, exist_ok=True)
    latest_file = os.path.join(latest_dir, "visualization.html")
    shutil.copy(output_file, latest_file)
    print(f"✓ Visualização disponível em: {latest_file}")

if __name__ == "__main__":
    generate_interactive_plot()
