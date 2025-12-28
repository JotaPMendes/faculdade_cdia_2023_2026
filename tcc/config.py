CONFIG = {
    # --- Problema e Malha ---
    "problem": "electrostatic_mesh",
    "mesh_file": "meshes/files/stator.msh",
    
    # --- Parâmetros de Treino ---
    "N_data": 5000,
    "N_test": 2500,
    "keep_checkpoints": 3,
    "use_mesh": True,
    
    # --- Condições de Contorno (Genérico) ---
    # Mapeia nome do Physical Group -> Valor do Potencial (Normalizado 0-1)
    "boundary_conditions": {
        "Outer": 0.0,   # Stator Ground
        "Inner": 1.0,   # Stator High Potential
        "Top": 1.0,     # L-Shape Top
        "Bottom": 0.0,  # L-Shape Bottom
        "Left": 0.0,    # L-Shape Left
        "Right": 0.0,   # L-Shape Right
        "Inner_L": 0.0  # L-Shape Inner
    },
    
    # --- Parâmetros de Visualização ---
    "scaling_factor": 100.0, # Multiplicador para output (1.0 -> 100V)
    
    # Definição do Slice 1D para o Relatório
    # Se "radial", usa raio (r_start, r_end)
    # Se "linear", usa coordenadas (p_start, p_end)
    "slice_config": {
        "type": "radial", # ou "linear"
        "p_start": [0.5, 0.0], # Início (x, y)
        "p_end": [1.0, 0.0],   # Fim (x, y)
        "xlabel": "Raio (r)"
    }
}
