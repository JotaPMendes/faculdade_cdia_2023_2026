import deepxde as dde
import numpy as np
import tensorflow as tf
from utils.mesh_loader import MeshLoader
from solver import ElectrostaticElement
import meshio

def create_electrostatic_mesh_problem(config):
    """
    Cria um problema Eletrostático 2D usando uma malha externa (.msh).
    Equação: -Laplacian(V) = rho/eps (Aqui assumindo rho=0 -> Laplace)
    """
    mesh_file = config.get("mesh_file", "domain.msh")
    loader = MeshLoader(mesh_file)
    
    # 1. Geometria
    domain_points = loader.get_all_points()
    geom = dde.geometry.PointCloud(domain_points, boundary_points=None)
    
    # Calcular Bounding Box da malha para ajustar Configuração
    xmin, ymin = domain_points.min(axis=0)
    xmax, ymax = domain_points.max(axis=0)
    Lx_mesh = xmax - xmin
    Ly_mesh = ymax - ymin
    
    print(f"✓ Malha carregada: Bounds [{xmin:.2f}, {xmax:.2f}] x [{ymin:.2f}, {ymax:.2f}]")
    print(f"✓ Ajustando CONFIG: Lx={Lx_mesh:.2f}, Ly={Ly_mesh:.2f}")
    
    # Atualizar Config Global (Side-effect intencional para alinhar plots)
    config["Lx"] = float(Lx_mesh)
    config["Ly"] = float(Ly_mesh)
    config["train_box"] = [float(xmin), float(ymin), float(xmax), float(ymax)]
    
    # 2. Equação Diferencial (Laplace)
    # d2V/dx2 + d2V/dy2 = 0
    def pde(x, y):
        dy_xx = dde.grad.hessian(y, x, i=0, j=0)
        dy_yy = dde.grad.hessian(y, x, i=1, j=1)
        return -dy_xx - dy_yy

    # 3. Condições de Contorno
    # Mapear nomes físicos para valores de potencial
    # Exemplo baseado no notebook do professor (MEF.ipynb):
    # Top: 100V, Outros: 0V
    bcs = []
    bc_configs = {
        "Top": 100.0,
        "Bottom": 0.0,
        "Left": 0.0,
        "Right": 0.0
    }
    
    # Para o solver FEM
    fem_boundary_conditions = {}

    for name, val in bc_configs.items():
        points = loader.get_boundary_points(name)
        if len(points) > 0:
            # DeepXDE BC
            values = np.full((len(points), 1), val)
            bc = dde.icbc.PointSetBC(points, values)
            bcs.append(bc)
            
            # FEM BC (armazenar nodes ids)
            # MeshLoader.boundary_nodes tem os índices
            if name in loader.boundary_nodes:
                fem_boundary_conditions[name] = {
                    'nodes': list(loader.boundary_nodes[name]),
                    'potential': val
                }
            
            print(f"✓ BC '{name}' carregada: {val}V ({len(points)} pontos).")

    # 4. Dados DeepXDE
    data = dde.data.PDE(
        geom,
        pde,
        bcs,
        num_domain=len(domain_points),
        num_boundary=0,
        num_test=1000,
        train_distribution="pseudo"
    )
    
    # Rede Neural
    net = dde.nn.MsFFN(
        [2] + [50] * 4 + [1],
        "tanh",
        "Glorot normal",
        sigmas=[1, 5, 10]
    )
    
    # 5. Preparar dados para o Solver FEM (Professor)
    # Precisamos reconstruir a conectividade dos elementos
    mesh = meshio.read(loader.filename)
    
    points = mesh.points[:, :2] # (N, 2)
    triangles = mesh.cells_dict.get('triangle', [])
    
    # Criar elementos do solver
    elements = [ElectrostaticElement() for _ in range(len(triangles))]
    for element, tri in zip(elements, triangles):
        element.setNodes(*points[tri].T)
        
    # Estrutura para o solver
    fem_data = {
        "nodes": points,
        "nodeTags": np.arange(len(points)), # Assumindo sequencial 0..N-1
        "triElements": triangles,
        "elements": elements,
        "boundaryConditions": fem_boundary_conditions
    }
    
    return {
        "data": data,
        "net": net,
        "kind": "electrostatic",
        "fem_data": fem_data, # Dados extras para o solver FEM
        "u_true": None # Não temos solução analítica
    }
