import json
import os

# Caminho para o arquivo JSON
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

def load_config(path=None):
    target_path = path if path else CONFIG_PATH
    if os.path.exists(target_path):
        with open(target_path, "r") as f:
            return json.load(f)
    else:
        # Fallback defaults
        return {
            "problem": "electrostatic_mesh",
            "mesh_file": "meshes/files/plate_holes.msh",
            "N_data": 10000,
            "N_test": 2500,
            "keep_checkpoints": 3,
            "use_mesh": True,
            "boundary_conditions": {"Left": 1.0, "Right": 0.0},
            "scaling_factor": 100.0,
            "slice_config": {"type": "linear"}
        }

# Alias para manter compatibilidade com main.py
load_config_from_json = load_config
CONFIG = load_config()
