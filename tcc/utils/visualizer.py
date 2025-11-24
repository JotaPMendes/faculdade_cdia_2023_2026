import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import meshio
import os
import sys
from scipy.interpolate import griddata

# Adicionar raiz ao path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import CONFIG
from main import get_problem
from models.pinn import train_pinn
from models.fem import PoissonFEM
from solver import ElectrostaticSolver
from utils.checkpoint import CheckpointManager

def generate_interactive_plot(run_dir=None):
    print("="*50)
    print("GERADOR DE VISUALIZAÇÃO INTERATIVA (PLOTLY)")
    print("="*50)

    # 1. Carregar Configuração e Problema
    problem = get_problem(CONFIG)
    
    # Se run_dir não for especificado, descobrir via CheckpointManager
    if run_dir is None:
        ckpt_manager = CheckpointManager()
        run_dir = ckpt_manager.get_run_dir(CONFIG)
        print(f"✓ Diretório detectado automaticamente: {run_dir}")
    
    # 2. Carregar Malha (FEM)
    mesh_file = CONFIG["mesh_file"]
    mesh = meshio.read(mesh_file)
    points = mesh.points[:, :2]
    triangles = mesh.cells_dict.get("triangle")
    
    print(f"✓ Malha carregada: {len(points)} nós, {len(triangles)} elementos.")

    # 3. Carregar Modelos
    # PINN
    print("Carregando PINN...")
    model_pinn = train_pinn(problem, CONFIG) 
    
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
    
    # 4. Preparar Dados para Plotagem 2D (Heatmap)
    print("Gerando grid de alta resolução...")
    xmin, ymin, xmax, ymax = CONFIG["train_box"]
    N_grid = 400 # Resolução do grid
    gx = np.linspace(xmin, xmax, N_grid)
    gy = np.linspace(ymin, ymax, N_grid)
    GX, GY = np.meshgrid(gx, gy)
    Grid_points = np.stack([GX.ravel(), GY.ravel()], axis=1)
    
    # Máscara L-Shape
    mask_valid = ~((Grid_points[:,0] > 0) & (Grid_points[:,1] > 0))
    valid_points = Grid_points[mask_valid]
    
    # Fator de escala
    scale = problem.get("scaling_factor", 1.0)
    
    # A) PINN 2D
    U_pinn_flat = np.nan * np.ones(len(Grid_points))
    if len(valid_points) > 0:
        U_pinn_valid = model_pinn.predict(valid_points).ravel()
        U_pinn_flat[mask_valid] = U_pinn_valid * scale
    U_pinn_grid = U_pinn_flat.reshape(N_grid, N_grid)
    
    # B) FEM 2D (Interpolação Linear)
    print("Interpolando FEM para grid...")
    # points: (N_nodes, 2), fem_potential: (N_nodes,)
    # Grid_points: (N_grid*N_grid, 2)
    U_fem_flat = griddata(points, fem_potential, Grid_points, method='linear')
    # Aplicar máscara (griddata pode extrapolar ou dar nan fora do convex hull, mas L-shape é concavo)
    # Vamos forçar nan onde é inválido geometricamente
    U_fem_flat[~mask_valid] = np.nan
    U_fem_grid = U_fem_flat.reshape(N_grid, N_grid)

    # 5. Preparar Dados para Slice 1D (Zoom Infinito)
    print("Gerando Slice 1D...")
    # Diagonal aproximando a singularidade: (-0.5, -0.5) -> (0, 0)
    # Vamos passar um pouco do zero para ver o comportamento
    p_start = np.array([-0.5, -0.5])
    p_end = np.array([0.0, 0.0]) # Singularidade exata
    
    N_slice = 200
    t = np.linspace(0, 1, N_slice)
    slice_points = p_start + np.outer(t, (p_end - p_start))
    
    # Distância da origem (para eixo X do plot)
    dist = np.linalg.norm(slice_points, axis=1)
    # Inverter para que 0 seja a singularidade? Ou manter distância da origem?
    # Vamos usar coordenada x (já que é diagonal y=x)
    slice_x = slice_points[:, 0]
    
    # PINN Slice
    slice_pinn = model_pinn.predict(slice_points).ravel() * scale
    
    # FEM Slice (Interpolação)
    slice_fem = griddata(points, fem_potential, slice_points, method='linear')

    # --- PLOTLY SUBPLOTS ---
    fig = make_subplots(
        rows=1, cols=2,
        column_widths=[0.6, 0.4],
        subplot_titles=("Comparação 2D: PINN (Esquerda) vs FEM (Direita)", "Zoom 1D: Suavidade vs Discretização"),
        specs=[[{"type": "contour"}, {"type": "xy"}]]
    )

    # 1. Heatmap Combinado (Truque: Usar botões para alternar ou sobrepor?)
    # Vamos fazer algo melhor: Botões para trocar o Heatmap 2D
    # Por padrão mostramos PINN.
    
    # Trace 0: PINN 2D
    fig.add_trace(go.Contour(
        z=U_pinn_grid, x=gx, y=gy,
        colorscale='Viridis',
        contours=dict(start=0, end=100, size=2, showlines=False),
        colorbar=dict(title="V (PINN)", x=0.55, len=0.5, y=0.8),
        name='PINN 2D',
        visible=True
    ), row=1, col=1)
    
    # Trace 1: FEM 2D (Inicialmente oculto)
    fig.add_trace(go.Contour(
        z=U_fem_grid, x=gx, y=gy,
        colorscale='Viridis',
        contours=dict(start=0, end=100, size=2, showlines=False),
        colorbar=dict(title="V (FEM)", x=0.55, len=0.5, y=0.2),
        name='FEM 2D',
        visible=False
    ), row=1, col=1)

    # Trace 2: Slice PINN
    fig.add_trace(go.Scatter(
        x=slice_x, y=slice_pinn,
        mode='lines',
        name='PINN (Contínuo)',
        line=dict(color='cyan', width=3)
    ), row=1, col=2)
    
    # Trace 3: Slice FEM
    fig.add_trace(go.Scatter(
        x=slice_x, y=slice_fem,
        mode='lines+markers',
        name='FEM (Discreto)',
        line=dict(color='orange', width=1, dash='dot'),
        marker=dict(size=4)
    ), row=1, col=2)

    # Layout e Menus
    fig.update_layout(
        title="Prova de Conceito: Infinite Zoom (PINN) vs Discretização (FEM)",
        template="plotly_dark",
        height=700,
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                buttons=list([
                    dict(
                        args=[{"visible": [True, False, True, True]}],
                        label="Ver PINN 2D",
                        method="update"
                    ),
                    dict(
                        args=[{"visible": [False, True, True, True]}],
                        label="Ver FEM 2D",
                        method="update"
                    )
                ]),
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.05,
                xanchor="left",
                y=1.15,
                yanchor="top"
            ),
        ]
    )
    
    # Anotações
    fig.add_annotation(
        x=0, y=0, xref="x1", yref="y1",
        text="Singularidade (0,0)", showarrow=True, arrowhead=1, ax=40, ay=-40
    )
    
    fig.update_xaxes(title_text="X", row=1, col=1)
    fig.update_yaxes(title_text="Y", row=1, col=1)
    fig.update_xaxes(title_text="Posição X (Diagonal)", row=1, col=2)
    fig.update_yaxes(title_text="Potencial (V)", row=1, col=2)

    output_file = os.path.join(run_dir, "interactive_comparison_v2.html")
    fig.write_html(output_file)
    print(f"✓ Visualização salva em: {output_file}")

if __name__ == "__main__":
    generate_interactive_plot()
