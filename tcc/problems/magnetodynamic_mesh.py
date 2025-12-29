import deepxde as dde
import numpy as np
import tensorflow as tf
from utils.mesh_loader import MeshLoader
from solver import MagnetodynamicElement
import meshio

def create_magnetodynamic_mesh_problem(config):
    """
    Cria um problema Magnetodinâmico 2D usando uma malha externa (.msh).
    Equação: Laplacian(A) - j * omega * sigma * mu * A = -mu * J
    Separado em Parte Real e Imaginária.
    """
    mesh_file = config.get("mesh_file", "domain.msh")
    loader = MeshLoader(mesh_file)
    
    # Parâmetros Físicos
    f = config.get("frequency", 60.0)
    omega = 2 * np.pi * f
    sigma = config.get("sigma", 5.8e7) # Cobre
    mu_r = config.get("mu", 1.0)
    mu0 = 4 * np.pi * 1e-7
    mu = mu_r * mu0
    
    # Constante k^2 = j * omega * sigma * mu
    # No domínio da frequência: Laplacian(A) - j*k2*A = -mu*J
    # k2 = omega * sigma * mu
    k2 = omega * sigma * mu
    
    print(f"✓ Magnetodinâmica: f={f}Hz, sigma={sigma:.2e}, mu_r={mu_r}")
    
    # 1. Geometria
    domain_points = loader.get_all_points()
    mask_singularity = ~((np.abs(domain_points[:,0]) < 1e-6) & (np.abs(domain_points[:,1]) < 1e-6))
    domain_points = domain_points[mask_singularity]
    
    geom = dde.geometry.PointCloud(domain_points, boundary_points=None)
    
    xmin, ymin = domain_points.min(axis=0)
    xmax, ymax = domain_points.max(axis=0)
    config["Lx"] = float(xmax - xmin)
    config["Ly"] = float(ymax - ymin)
    config["train_box"] = [float(xmin), float(ymin), float(xmax), float(ymax)]
    
    # 2. Equação Diferencial (Acoplada Real/Imag)
    # A = Ar + j*Ai
    # Laplacian(Ar + jAi) - j*k2*(Ar + jAi) = 0 (Assumindo J=0)
    # (Laplacian(Ar) + k2*Ai) + j(Laplacian(Ai) - k2*Ar) = 0
    # Eq1: Laplacian(Ar) + k2*Ai = 0
    # Eq2: Laplacian(Ai) - k2*Ar = 0
    
    def pde(x, y):
        Ar = y[:, 0:1]
        Ai = y[:, 1:2]
        
        dAr_xx = dde.grad.hessian(y, x, component=0, i=0, j=0)
        dAr_yy = dde.grad.hessian(y, x, component=0, i=1, j=1)
        
        dAi_xx = dde.grad.hessian(y, x, component=1, i=0, j=0)
        dAi_yy = dde.grad.hessian(y, x, component=1, i=1, j=1)
        
        eq1 = (dAr_xx + dAr_yy) + k2 * Ai
        eq2 = (dAi_xx + dAi_yy) - k2 * Ar
        
        return [eq1, eq2]
 
    # 3. Condições de Contorno
    bcs = []
    A_MAX = config.get("scaling_factor", 1.0)
    bc_configs = config.get("boundary_conditions", {})
    fem_boundary_conditions = {}

    for name, val in bc_configs.items():
        points = loader.get_boundary_points(name)
        if len(points) > 0:
            # DeepXDE BC (Real e Imag)
            # Assumindo BC constante real para simplificar, ou zero.
            values = np.full((len(points), 1), val)
            zeros = np.zeros((len(points), 1))
            
            # Dirichlet para Ar
            bc_r = dde.icbc.PointSetBC(points, values, component=0)
            # Dirichlet para Ai (Zero)
            bc_i = dde.icbc.PointSetBC(points, zeros, component=1)
            
            bcs.append(bc_r)
            bcs.append(bc_i)
            
            # FEM BC
            if name in loader.boundary_nodes:
                fem_boundary_conditions[name] = {
                    'nodes': list(loader.boundary_nodes[name]),
                    'potential': complex(val * A_MAX, 0)
                }
            
            print(f"✓ BC '{name}' carregada.")

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
    
    # Rede Neural (2 saídas: Ar, Ai)
    net = dde.nn.FNN(
        [2] + [64] * 5 + [2],
        "tanh",
        "Glorot normal"
    )
    
    # 5. Preparar dados para o Solver FEM
    mesh = meshio.read(loader.filename)
    points = mesh.points[:, :2]
    triangles = mesh.cells_dict.get('triangle', [])
    
    elements = [MagnetodynamicElement() for _ in range(len(triangles))]
    for element, tri in zip(elements, triangles):
        element.setNodes(*points[tri].T)
        # Definir propriedades do material para cada elemento
        # Aqui assumindo homogêneo, mas poderia vir de tags físicas da malha
        element.setProperties(mu, 0, sigma) # J=0
        
    fem_data = {
        "nodes": points,
        "nodeTags": np.arange(len(points)),
        "triElements": triangles,
        "elements": elements,
        "boundaryConditions": fem_boundary_conditions,
        "frequency": f
    }
    
    pinn_config = {
        "arch_type": "FNN",
        "layers": [2] + [64]*5 + [2],
        "activation": "tanh",
        "initializer": "Glorot normal",
        "train_steps_adam": 30000,
        "train_steps_lbfgs": 10000
    }
    
    return {
        "data": data,
        "net": net,
        "kind": "magnetodynamic",
        "fem_data": fem_data,
        "u_true": None,
        "use_mesh": True,
        "pinn_config": pinn_config,
        "scaling_factor": A_MAX
    }
