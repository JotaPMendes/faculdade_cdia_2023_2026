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
from solver import ElectrostaticSolver
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
    
    # 2. Carregar Malha (FEM)
    mesh_file = config["mesh_file"]
    mesh = meshio.read(mesh_file)
    points = mesh.points[:, :2]
    triangles = mesh.cells_dict.get("triangle")
    
    # 3. Carregar Modelos e Dados
    # PINN
    if pinn_instance is not None:
        model_pinn = pinn_instance
    else:
        pinn = PINN(config, problem)
        pinn.train() 
        model_pinn = pinn
    
    # FEM
    print("Resolvendo FEM...")
    fem_data = problem["fem_data"]
    solver = ElectrostaticSolver(
        fem_data["nodes"],
        fem_data["nodeTags"],
        fem_data["triElements"],
        fem_data["elements"],
        fem_data["boundaryConditions"]
    )
    solver.assemble_global_matrix_and_vector()
    solver.apply_boundary_conditions()
    solver.solve()
    fem_potential = solver.get_potential()
    
    # 4. Preparar Dados 2D
    scale = problem.get("scaling_factor", 1.0)
    U_pinn = model_pinn.predict(points).ravel() * scale
    U_fem = fem_potential * 1.0 
    U_error = np.abs(U_pinn - U_fem)
    
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
    
    slice_pinn = model_pinn.predict(slice_points).ravel() * scale
    slice_fem = griddata(points, fem_potential, slice_points, method='linear')
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
                flatshading=False, # Restore 3D shading
                # lighting removed to allow default 3D look
            )
        else:
            return go.Scatter(
                x=points[:, 0], y=points[:, 1],
                mode='markers',
                marker=dict(size=4, color=values, colorscale=colorscale, showscale=True),
                name=name, visible=visible
            )

    # Determine ranges for consistent colorbar
    v_min, v_max = min(U_fem.min(), U_pinn.min()), max(U_fem.max(), U_pinn.max())
    
    # 1. PINN Map
    fig.add_trace(create_mesh_trace(U_pinn, "V (PINN)", True, 'Viridis', v_min, v_max), row=1, col=1)
    # 2. FEM Map
    fig.add_trace(create_mesh_trace(U_fem, "V (FEM)", False, 'Viridis', v_min, v_max), row=1, col=1)
    # 3. Error Map
    fig.add_trace(create_mesh_trace(U_error, "Erro Abs (V)", False, 'Magma'), row=1, col=1)

    # 4. Slice Line on Map (Visual Reference)
    fig.add_trace(go.Scatter3d(
        x=slice_points[:, 0], y=slice_points[:, 1], z=np.ones_like(slice_x)*0.01, # Slightly above
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
        line=dict(color='#00FFFF', width=3), # Cyan solid
    ), row=1, col=2)
    
    # 6. FEM Slice
    fig.add_trace(go.Scatter(
        x=slice_x, y=slice_fem,
        mode='lines+markers',
        name='FEM',
        line=dict(color='#FFA500', width=2, dash='dot'), # Orange dotted
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
        paper_bgcolor="#1e1e1e", # Uniform dark background
        plot_bgcolor="#1e1e1e",
        height=850,
        margin=dict(t=100, b=50, l=50, r=50),
        legend=dict(x=0.55, y=1.02, orientation="h"),
        
        # 3D Scene - Unlocked
        scene=dict(
            xaxis=dict(title='X (m)', showgrid=True, zeroline=False),
            yaxis=dict(title='Y (m)', showgrid=True, zeroline=False),
            zaxis=dict(title='', showticklabels=False, range=[-1, 1], showgrid=True),
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.5), # Default 3D perspective
                up=dict(x=0, y=0, z=1)
            ),
            aspectmode='data',
            dragmode='orbit' # Better for 3D rotation
        )
    )

    # Axis Labels
    fig.update_xaxes(title_text=xlabel, row=1, col=2)
    fig.update_yaxes(title_text="Potencial Elétrico (V)", row=1, col=2)
    
    fig.update_xaxes(title_text=xlabel, row=2, col=2)
    fig.update_yaxes(title_text="Erro Absoluto (V)", row=2, col=2)

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
                         args=[{"visible": [True, False, False, True, True, True, True]}, # Map traces
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

    # Save
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
