from .heat import create_heat_problem
from .wave import create_wave_problem
from .poisson2d import create_poisson_2d_problem
from .custom_mesh import create_custom_mesh_problem
from .heat_mesh import create_heat_mesh_problem

def make_problem(cfg):
    if cfg["problem"] == "heat_1d":
        return create_heat_problem(cfg)
    elif cfg["problem"] == "wave_1d":
        return create_wave_problem(cfg)
    elif cfg["problem"] == "poisson_2d":
        return create_poisson_2d_problem(cfg)
    elif cfg["problem"] == "custom_mesh":
        return create_custom_mesh_problem(cfg)
    elif cfg["problem"] == "heat_mesh":
        return create_heat_mesh_problem(cfg)
    else:
        raise ValueError(f"Problema '{cfg['problem']}' não implementado.")