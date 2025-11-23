import numpy as np
import deepxde as dde
import tensorflow as tf

def create_wave_problem(cfg):
    c, Lx, T_train = cfg["c"], cfg["Lx"], cfg["T_train"]

    def u_true(X):
        x, t = X[:, 0:1], X[:, 1:2]
        k = np.pi / Lx
        return np.sin(k * x) * np.cos(c * k * t)

    def pde(X, y):
        u_tt = dde.grad.hessian(y, X, i=0, j=1)
        u_xx = dde.grad.hessian(y, X, i=0, j=0)
        return u_tt - (c**2) * u_xx

    geom = dde.geometry.Interval(0.0, Lx)
    timedomain = dde.geometry.TimeDomain(0.0, T_train)
    geomtime = dde.geometry.GeometryXTime(geom, timedomain)

    bcL = dde.icbc.DirichletBC(geomtime, lambda X: 0.0, lambda X, on_b: on_b and np.isclose(X[0], 0.0))
    bcR = dde.icbc.DirichletBC(geomtime, lambda X: 0.0, lambda X, on_b: on_b and np.isclose(X[0], Lx))
    ic_u = dde.icbc.IC(geomtime, lambda X: np.sin(np.pi*X[:,0:1]/Lx), lambda X, on_i: on_i)
    
    def operator_bc(X, y, _):
        return dde.grad.jacobian(y, X, i=0, j=1) # du/dt
    ic_ut = dde.icbc.OperatorBC(geomtime, operator_bc, lambda X, on_i: np.isclose(X[1], 0.0))

    data = dde.data.TimePDE(geomtime, pde, [bcL, bcR, ic_u, ic_ut],
                            num_domain=8000, num_boundary=800, num_initial=800, num_test=1000)

    net = dde.nn.FNN([2] + [64]*5 + [1], "sin", "Glorot uniform") # Sin activation p/ onda costuma ser melhor
    def feature_transform(X):
        x_norm = 2.0 * (X[:, 0:1] / Lx) - 1.0
        t_norm = 2.0 * (X[:, 1:2] / T_train) - 1.0
        return tf.concat([x_norm, t_norm], axis=1)
    net.apply_feature_transform(feature_transform)

    return dict(kind="time", u_true=u_true, data=data, net=net)