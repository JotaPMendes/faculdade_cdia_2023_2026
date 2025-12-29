import deepxde as dde
import numpy as np
import tensorflow as tf
from utils.mesh_loader import MeshLoader
from solver import MagnetostaticElement
import meshio

def create_magnetostatic_mesh_problem(config):
    """
    Cria um problema Magnetostático 2D usando uma malha externa (.msh).
    Equação: -Laplacian(A) = mu * J (Aqui assumindo J=0 -> Laplace)
    """
    mesh_file = config.get("mesh_file", "domain.msh")
    loader = MeshLoader(mesh_file)
    
    # 1. Geometria
    domain_points = loader.get_all_points()
    
    # Filtrar singularidade exata (0,0) para evitar gradientes infinitos
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
    
    # Atualizar Config Global
    config["Lx"] = float(Lx_mesh)
    config["Ly"] = float(Ly_mesh)
    config["train_box"] = [float(xmin), float(ymin), float(xmax), float(ymax)]
    
    # 2. Equação Diferencial (Laplace para Potencial Magnético A)
    # d2A/dx2 + d2A/dy2 = 0 (Assumindo J=0 na região de ar/ferro sem fonte)
    def pde(x, y):
        dA_xx = dde.grad.hessian(y, x, i=0, j=0)
        dA_yy = dde.grad.hessian(y, x, i=1, j=1)
        return -dA_xx - dA_yy
 
    # 3. Condições de Contorno
    bcs = []
    
    # Fator de escala para visualização (A pode ser pequeno)
    A_MAX = config.get("scaling_factor", 1.0)
    
    bc_configs = config.get("boundary_conditions", {})
    
    fem_boundary_conditions = {}

    for name, val in bc_configs.items():
        points = loader.get_boundary_points(name)
        if len(points) > 0:
            # DeepXDE BC
            values = np.full((len(points), 1), val)
            bc = dde.icbc.PointSetBC(points, values)
            bcs.append(bc)
            
            # FEM BC
            if name in loader.boundary_nodes:
                fem_boundary_conditions[name] = {
                    'nodes': list(loader.boundary_nodes[name]),
                    'potential': val * A_MAX
                }
            
            print(f"✓ BC '{name}' carregada: {val} (PINN) / {val*A_MAX} (FEM) ({len(points)} pontos).")

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
    net = dde.nn.FNN(
        [2] + [50] * 4 + [1],
        "tanh",
        "Glorot normal"
    )
    
    # 5. Preparar dados para o Solver FEM
    mesh = meshio.read(loader.filename)
    points = mesh.points[:, :2]
    triangles = mesh.cells_dict.get('triangle', [])
    
    elements = [MagnetostaticElement() for _ in range(len(triangles))]
    for element, tri in zip(elements, triangles):
        element.setNodes(*points[tri].T)
        
    fem_data = {
        "nodes": points,
        "nodeTags": np.arange(len(points)),
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
        "kind": "magnetostatic",
        "fem_data": fem_data,
        "u_true": None,
        "use_mesh": True,
        "pinn_config": pinn_config,
        "scaling_factor": A_MAX
    }
