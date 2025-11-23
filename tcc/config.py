CONFIG = {
    "problem": "heat_mesh",
    "mesh_file": "domain.msh", # MeshLoader will look in meshes/
    "alpha": 0.1,              # Difusividade
    "c": 1.0,                  # Velocidade da onda
    "Lx": 4.0,
    "T_train": 8.0,
    "T_eval": 16.0,
    "N_data": 5000,            # Amostras ML Clássico
    "x0_list" : [0.2, 0.4, 0.6, 0.8],
    "Nx_train": 60, 
    "Ny_train": 60,
    "train_box": [0.0, 0.0, 0.6, 1.0] # [xmin, ymin, xmax, ymax]
}