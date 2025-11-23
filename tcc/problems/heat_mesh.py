import deepxde as dde
import numpy as np
import tensorflow as tf
from utils.mesh_loader import MeshLoader

def create_heat_mesh_problem(config):
    """
    Cria um problema de Calor 2D (Estacionário) usando uma malha externa (.msh).
    Equação: -Laplacian(u) = 0 (sem fonte interna, apenas BCs)
    """
    mesh_file = config.get("mesh_file", "domain.msh")
    loader = MeshLoader(mesh_file)
    
    # 1. Geometria
    domain_points = loader.get_all_points()
    geom = dde.geometry.PointCloud(domain_points, boundary_points=None)
    
    # 2. Equação Diferencial (Laplace/Calor Estacionário)
    # -Laplacian(u) = 0
    def pde(x, y):
        dy_xx = dde.grad.hessian(y, x, i=0, j=0)
        dy_yy = dde.grad.hessian(y, x, i=1, j=1)
        return -dy_xx - dy_yy

    # 3. Condições de Contorno
    bcs = []
    
    # Exemplo: Topo quente (1.0), resto frio (0.0)
    for name in ["Top", "Bottom", "Left", "Right"]:
        points = loader.get_boundary_points(name)
        if len(points) > 0:
            if name == "Top":
                values = np.ones((len(points), 1))
            else:
                values = np.zeros((len(points), 1))
            
            bc = dde.icbc.PointSetBC(points, values)
            bcs.append(bc)
            print(f"✓ BC '{name}' carregada com {len(points)} pontos (Heat).")

    # 4. Dados
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
    
    return {
        "data": data,
        "net": net,
        "kind": "space"
    }
