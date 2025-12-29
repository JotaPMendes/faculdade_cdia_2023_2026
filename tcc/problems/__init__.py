from .heat import create_heat_problem
from .wave import create_wave_problem
from .poisson2d import create_poisson_2d_problem
from .electrostatic_mesh import create_electrostatic_mesh_problem
from .magnetostatic_mesh import create_magnetostatic_mesh_problem
from .magnetodynamic_mesh import create_magnetodynamic_mesh_problem

def get_problem(cfg):
    if cfg["problem"] == "heat_1d":
        return create_heat_problem(cfg)
    elif cfg["problem"] == "wave_1d":
        return create_wave_problem(cfg)
    elif cfg["problem"] == "poisson_2d":
        return create_poisson_2d_problem(cfg)
    elif cfg["problem"] == "electrostatic_mesh":
        return create_electrostatic_mesh_problem(cfg)
    elif cfg["problem"] == "magnetostatic_mesh":
        return create_magnetostatic_mesh_problem(cfg)
    elif cfg["problem"] == "magnetodynamic_mesh":
        return create_magnetodynamic_mesh_problem(cfg)
    else:
        raise ValueError(f"Problema '{cfg['problem']}' não implementado.")