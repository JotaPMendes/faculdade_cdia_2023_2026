from .heat import make_heat_1d
from .wave import make_wave_1d
from .poisson2d import make_poisson_2d

def make_problem(cfg):
    if cfg["problem"] == "heat_1d":
        return make_heat_1d(cfg)
    elif cfg["problem"] == "wave_1d":
        return make_wave_1d(cfg)
    elif cfg["problem"] == "poisson_2d":
        return make_poisson_2d(cfg)
    else:
        raise ValueError(f"Problema '{cfg['problem']}' não implementado.")