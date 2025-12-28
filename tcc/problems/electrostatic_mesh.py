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
    
    # Filtrar singularidade exata (0,0) para evitar gradientes infinitos
    # Tolerância pequena para garantir
    mask_singularity = ~((np.abs(domain_points[:,0]) < 1e-6) & (np.abs(domain_points[:,1]) < 1e-6))
    domain_points = domain_points[mask_singularity]
    
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

    # 3. Condições de Contorno (Dinâmico via Config)
    bcs = []
    
    # Normalização: Trabalhar com [0, 1] e reescalar na visualização
    V_MAX = config.get("scaling_factor", 100.0)
    
    bc_configs = config.get("boundary_conditions", {})
    
    fem_boundary_conditions = {}

    for name, val in bc_configs.items():
        points = loader.get_boundary_points(name)
        if len(points) > 0:
            # DeepXDE BC (Normalizado)
            values = np.full((len(points), 1), val)
            bc = dde.icbc.PointSetBC(points, values)
            bcs.append(bc)
            
            # FEM BC (Escala Real = val * V_MAX)
            if name in loader.boundary_nodes:
                fem_boundary_conditions[name] = {
                    'nodes': list(loader.boundary_nodes[name]),
                    'potential': val * V_MAX
                }
            
            print(f"✓ BC '{name}' carregada: {val} (PINN) / {val*V_MAX}V (FEM) ({len(points)} pontos).")

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
    
    # Otimização: FNN profunda é robusta para geometria complexa
    # MsFFN pode ser instável se não calibrada, FNN é mais segura aqui.
    net = dde.nn.FNN(
        [2] + [50] * 4 + [1],
        "tanh",
        "Glorot normal"
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
    
    pinn_config = {
        "arch_type": "FNN",
        "layers": [2] + [50]*4 + [1],
        "activation": "tanh",
        "initializer": "Glorot normal",
        "train_steps_adam": 20000,
        "train_steps_lbfgs": 10000
    }
    
    return {
        "data": data,
        "net": net,
        "kind": "electrostatic",
        "fem_data": fem_data, # Dados extras para o solver FEM
        "u_true": None, # Não temos solução analítica
        "use_mesh": True,
        "pinn_config": pinn_config,
        "scaling_factor": V_MAX # Passar fator de escala para visualizador
    }
