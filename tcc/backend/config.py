CONFIG = {
    "problem": "electrostatic_mesh",
    "mesh_file": "meshes/files/plate_holes.msh",
    "N_data": 10000,
    "N_test": 2500,
    "keep_checkpoints": 3,
    "use_mesh": True,
    "boundary_conditions": {
    "Left": 1.0,
    "Right": 0.0,
    "Top": 0.0,
    "Bottom": 0.0,
    "Holes": 0.0
},
    "scaling_factor": 100.0,
    "slice_config": {
        "type": "radial",
        "p_start": [0.5, 0.0],
        "p_end": [1.0, 0.0],
        "xlabel": "Raio (r)"
    }
}
