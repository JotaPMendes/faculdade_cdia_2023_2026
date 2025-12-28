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
    print("GERADOR DE VISUALIZAÇÃO INTERATIVA (PLOTLY)")
    print("="*50)

    # 0. Usar config fornecida ou global
    if config is None:
        config = CONFIG

    # 1. Carregar Configuração e Problema
    problem = get_problem(config)
    
    # Se run_dir não for especificado, descobrir via CheckpointManager
    if run_dir is None:
        ckpt_manager = CheckpointManager()
        run_dir = ckpt_manager.get_run_dir(config)
        print(f"✓ Diretório detectado automaticamente: {run_dir}")
    
    # 2. Carregar Malha (FEM)
    mesh_file = config["mesh_file"]
    mesh = meshio.read(mesh_file)
    points = mesh.points[:, :2]
    triangles = mesh.cells_dict.get("triangle")
    
    print(f"✓ Malha carregada: {len(points)} nós, {len(triangles)} elementos.")

    # 3. Carregar Modelos
    # PINN
    if pinn_instance is not None:
        print("Usando instância PINN fornecida...")
        model_pinn = pinn_instance
    else:
        print("Carregando nova instância PINN...")
        pinn = PINN(config, problem)
        pinn.train() # Restores weights if available
        model_pinn = pinn
    
    # FEM
    print("Resolvendo FEM (para comparação)...")
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
    fem_potential = solver.get_potential() # Valores nos nós
    
    # 4. Preparar Dados para Plotagem (Geometry-Aware)
    print("Preparando plotagem baseada na malha (Geometry-Aware)...")
    
    # Fator de escala
    scale = problem.get("scaling_factor", 1.0)
    
    # A) PINN nos Nós
    U_pinn = model_pinn.predict(points).ravel() * scale
    
    # B) FEM nos Nós
    U_fem = fem_potential * 1.0 
    
    # C) Erro Absoluto
    U_error = np.abs(U_pinn - U_fem)
    
    # Preparar Triângulos para Plotly (i, j, k)
    if triangles is None:
        print("⚠ Aviso: Malha sem triângulos. Usando Scatter plot.")
        use_mesh_plot = False
    else:
        use_mesh_plot = True
        tri_i = triangles[:, 0]
        tri_j = triangles[:, 1]
        tri_k = triangles[:, 2]

    # 5. Preparar Dados para Slice 1D
    print("Gerando Slice 1D...")
    
    slice_cfg = config.get("slice_config", {
        "type": "linear",
        "p_start": [-0.5, -0.5],
        "p_end": [0.0, 0.0],
        "xlabel": "Posição"
    })
    
    p_start = np.array(slice_cfg["p_start"])
    p_end = np.array(slice_cfg["p_end"])
    xlabel = slice_cfg.get("xlabel", "Posição")
    
    N_slice = 200
    t = np.linspace(0, 1, N_slice)
    slice_points = p_start + np.outer(t, (p_end - p_start))
    
    if slice_cfg.get("type") == "radial":
        slice_x = np.linalg.norm(slice_points, axis=1)
    else:
        slice_x = np.linalg.norm(slice_points - p_start, axis=1)
    
    slice_pinn = model_pinn.predict(slice_points).ravel() * scale
    slice_fem = griddata(points, fem_potential, slice_points, method='linear')

    # --- PLOTLY SUBPLOTS ---
    fig = make_subplots(
        rows=1, cols=2,
        column_widths=[0.6, 0.4],
        subplot_titles=("Mapa 2D (Geometria Exata)", "Slice 1D (Detalhe)"),
        specs=[[{"type": "scene"}, {"type": "xy"}]]
    )

    def create_mesh_trace(values, name, visible, colorscale='Viridis'):
        if use_mesh_plot:
            return go.Mesh3d(
                x=points[:, 0],
                y=points[:, 1],
                z=np.zeros_like(points[:, 0]),
                i=tri_i,
                j=tri_j,
                k=tri_k,
                intensity=values,
                colorscale=colorscale,
                colorbar=dict(title=name, x=0.45),
                name=name,
                visible=visible,
                flatshading=True
            )
        else:
            return go.Scatter(
                x=points[:, 0],
                y=points[:, 1],
                mode='markers',
                marker=dict(
                    size=4,
                    color=values,
                    colorscale=colorscale,
                    colorbar=dict(title=name, x=0.45)
                ),
                name=name,
                visible=visible
            )

    fig.add_trace(create_mesh_trace(U_pinn, "V (PINN)", True), row=1, col=1)
    fig.add_trace(create_mesh_trace(U_fem, "V (FEM)", False), row=1, col=1)
    fig.add_trace(create_mesh_trace(U_error, "Erro Abs", False, colorscale='Hot'), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=slice_x, y=slice_pinn,
        mode='lines',
        name='PINN (Slice)',
        line=dict(color='cyan', width=3)
    ), row=1, col=2)
    
    fig.add_trace(go.Scatter(
        x=slice_x, y=slice_fem,
        mode='lines+markers',
        name='FEM (Slice)',
        line=dict(color='orange', width=1, dash='dot'),
        marker=dict(size=4)
    ), row=1, col=2)

    # Layout e Menus
    fig.update_layout(
        title=dict(
            text=f"Análise Geométrica: {os.path.basename(config['mesh_file'])}",
            y=0.98,
            x=0.5,
            xanchor='center',
            yanchor='top',
            font=dict(size=20)
        ),
        template="plotly_dark",
        height=800,
        margin=dict(t=120, b=50, l=50, r=50), # Mais espaço no topo
        scene=dict(
            xaxis=dict(title='X'),
            yaxis=dict(title='Y'),
            zaxis=dict(title='', showticklabels=False, range=[-1, 1]),
            camera=dict(eye=dict(x=0, y=0, z=2.2)),
            aspectmode='data' # Manter proporção correta
        ),
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                buttons=list([
                    dict(
                        args=[{"visible": [True, False, False, True, True]}],
                        label="PINN",
                        method="update"
                    ),
                    dict(
                        args=[{"visible": [False, True, False, True, True]}],
                        label="FEM",
                        method="update"
                    ),
                    dict(
                        args=[{"visible": [False, False, True, True, True]}],
                        label="ERRO",
                        method="update"
                    )
                ]),
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.0,
                xanchor="left",
                y=1.15, # Na margem superior, à esquerda
                yanchor="top",
                bgcolor="rgba(0,0,0,0.5)",
                font=dict(color="white")
            ),
        ],
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    fig.update_xaxes(title_text=xlabel, row=1, col=2)
    fig.update_yaxes(title_text="Potencial (V)", row=1, col=2)

    output_file = os.path.join(run_dir, "interactive_comparison_v2.html")
    fig.write_html(output_file)
    print(f"✓ Visualização salva em: {output_file}")
    
    # Copiar para results/latest
    latest_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", "latest")
    os.makedirs(latest_dir, exist_ok=True)
    latest_file = os.path.join(latest_dir, "visualization.html")
    shutil.copy(output_file, latest_file)
    print(f"✓ Visualização disponível em: {latest_file}")

if __name__ == "__main__":
    generate_interactive_plot()
