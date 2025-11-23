import numpy as np
import deepxde as dde
import tensorflow as tf

def create_heat_problem(cfg):
    alpha, Lx, T_train = cfg["alpha"], cfg["Lx"], cfg["T_train"]

    def u_true(X):
        x, t = X[:, 0:1], X[:, 1:2]
        k = np.pi / Lx
        return np.sin(k * x) * np.exp(-alpha * (k**2) * t)

    def pde(X, y):
        du_t  = dde.grad.jacobian(y, X, i=0, j=1)
        du_xx = dde.grad.hessian (y, X, i=0, j=0)
        return du_t - alpha * du_xx

    geom = dde.geometry.Interval(0.0, Lx)
    timedomain = dde.geometry.TimeDomain(0.0, T_train)
    geomtime = dde.geometry.GeometryXTime(geom, timedomain)

    bcL = dde.icbc.DirichletBC(geomtime, lambda X: 0.0, lambda X, on_b: on_b and np.isclose(X[0], 0.0))
    bcR = dde.icbc.DirichletBC(geomtime, lambda X: 0.0, lambda X, on_b: on_b and np.isclose(X[0], Lx))
    ic  = dde.icbc.IC(geomtime, lambda X: np.sin(np.pi*X[:,0:1]/Lx), lambda X, on_i: on_i)

    data = dde.data.TimePDE(geomtime, pde, [bcL, bcR, ic],
                            num_domain=4000, num_boundary=400, num_initial=400, num_test=1000)
    
    net = dde.nn.FNN([2] + [64]*4 + [1], "tanh", "Glorot uniform")
    def feature_transform(X):
        x_norm = 2.0 * (X[:, 0:1] / Lx) - 1.0
        t_norm = 2.0 * (X[:, 1:2] / T_train) - 1.0
        return tf.concat([x_norm, t_norm], axis=1)
    net.apply_feature_transform(feature_transform)

    return dict(kind="time", u_true=u_true, data=data, net=net)