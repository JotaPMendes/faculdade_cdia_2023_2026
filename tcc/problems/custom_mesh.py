import deepxde as dde
import numpy as np
import tensorflow as tf
from utils.mesh_loader import MeshLoader

def create_custom_mesh_problem(config):
    """
    Cria um problema de Poisson 2D usando uma malha externa (.msh).
    """
    mesh_file = config.get("mesh_file", "domain.msh")
    loader = MeshLoader(mesh_file)
    
    # 1. Geometria (Nuvem de Pontos)
    # Usamos todos os pontos da malha como "domínio" para amostragem
    # DeepXDE PointCloud aceita pontos de contorno também
    domain_points = loader.get_all_points()
    geom = dde.geometry.PointCloud(domain_points, boundary_points=None) # Boundary points handled separately via BCs
    
    # 2. Equação Diferencial (Poisson)
    # -Laplacian(u) = f
    def pde(x, y):
        dy_xx = dde.grad.hessian(y, x, i=0, j=0)
        dy_yy = dde.grad.hessian(y, x, i=1, j=1)
        
        # Fonte f(x,y)
        # Vamos assumir a mesma fonte do problema Poisson 2D original para comparação
        # f = 2*pi^2 * sin(pi*x)*sin(pi*y)
        f = 2 * np.pi**2 * tf.sin(np.pi * x[:, 0:1]) * tf.sin(np.pi * x[:, 1:2])
        
        return -dy_xx - dy_yy - f

    # 3. Condições de Contorno
    # Extrair pontos de cada borda física
    # Nomes devem bater com o arquivo .geo/.msh: "Top", "Bottom", "Left", "Right"
    
    bcs = []
    
    # Solução exata para BCs (Dirichlet)
    def u_true_func(x):
        return np.sin(np.pi * x[:, 0:1]) * np.sin(np.pi * x[:, 1:2])

    for name in ["Top", "Bottom", "Left", "Right"]:
        points = loader.get_boundary_points(name)
        if len(points) > 0:
            # Valores exatos nesses pontos
            values = u_true_func(points)
            
            # PointSetBC: Impõe valores em pontos específicos
            bc = dde.icbc.PointSetBC(points, values)
            bcs.append(bc)
            print(f"✓ BC '{name}' carregada com {len(points)} pontos.")
        else:
            print(f"⚠️ Aviso: Borda '{name}' não encontrada na malha.")

    # 4. Dados de Treino
    # PointCloud geometry já fornece os pontos.
    # Num_domain e num_boundary são ignorados se usarmos PointCloud com pontos fixos?
    # Não, PointCloud faz amostragem dos pontos fornecidos.
    
    data = dde.data.PDE(
        geom,
        pde,
        bcs,
        num_domain=len(domain_points), # Usar todos os pontos da malha
        num_boundary=0, # BCs são PointSetBC, não precisam de amostragem geométrica
        num_test=1000,  # Teste aleatório (ou poderíamos usar uma parte da malha)
        train_distribution="pseudo" # PointCloud usa pseudo por padrão para escolher dos pontos dados
    )
    
    # Rede Neural
    # Arquitetura MsFFN padrão
    net = dde.nn.MsFFN(
        [2] + [64] * 5 + [1],
        "tanh",
        "Glorot normal",
        sigmas=[1, 5, 10]
    )
    
    return {
        "data": data,
        "net": net,
        "u_true": lambda x: np.sin(np.pi * x[:, 0]) * np.sin(np.pi * x[:, 1]), # Para cálculo de erro
        "kind": "space"
    }
