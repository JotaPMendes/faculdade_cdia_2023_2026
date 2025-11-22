import numpy as np
import deepxde as dde
import tensorflow as tf

def make_poisson_2d(cfg):
    # CRÍTICO: Restringir geometria do PINN para ser justo com ML
    bx0, by0, bx1, by1 = cfg["train_box"]

    def u_true(X):
        x, y = X[:, 0:1], X[:, 1:2]
        return np.sin(np.pi * x) * np.sin(np.pi * y)

    def u_true_tf(X):
        x, y = X[:, 0:1], X[:, 1:2]
        return tf.sin(np.pi * x) * tf.sin(np.pi * y)

    def pde(X, y):
        u_xx = dde.grad.hessian(y, X, i=0, j=0)
        u_yy = dde.grad.hessian(y, X, i=1, j=1)
        f_tf = -2.0 * (np.pi**2) * u_true_tf(X) # f = -laplacian(u) -> laplacian(u) + f = 0
        return (u_xx + u_yy) - f_tf # deepxde minimiza abs(output)

    # Geometria restrita ao subdomínio de treino
    geom = dde.geometry.Rectangle([bx0, by0], [bx1, by1])
    
    # BC apenas nas bordas DA CAIXA DE TREINO
    # IMPORTANTE: Usar u_true para pegar os valores corretos na borda (especialmente em x=0.6)
    bc = dde.icbc.DirichletBC(geom, u_true, lambda X, on_b: on_b)

    # Pontos âncora (opcional, ajuda a fixar a solução)
    N_anchor = 200
    XY_anchor = np.random.rand(N_anchor, 2) * [bx1-bx0, by1-by0] + [bx0, by0]
    U_anchor = u_true(XY_anchor)
    anchor_bc = dde.icbc.PointSetBC(XY_anchor, U_anchor)

    data = dde.data.PDE(geom, pde, [bc, anchor_bc], 
                        num_domain=10000, num_boundary=2000, num_test=2000,
                        train_distribution="Sobol")

    # Rede Multi-scale com ativação tanh (mais estável com MsFFN) e mais escalas Fourier
    net = dde.nn.MsFFN([2] + [64]*5 + [1], "tanh", "Glorot uniform", sigmas=[1, 5, 10])
    
    # Feature transform (Normaliza [bx0, bx1] -> [-1, 1])
    def feature_transform(X):
        x_avg = (bx0 + bx1) / 2.0
        x_rad = (bx1 - bx0) / 2.0
        y_avg = (by0 + by1) / 2.0
        y_rad = (by1 - by0) / 2.0
        
        x = (X[:, 0:1] - x_avg) / x_rad
        y = (X[:, 1:2] - y_avg) / y_rad
        return tf.concat([x, y], axis=1)
    
    net.apply_feature_transform(feature_transform)

    return dict(kind="space", u_true=u_true, data=data, net=net)