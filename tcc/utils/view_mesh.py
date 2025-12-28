import meshio
import matplotlib.pyplot as plt
import numpy as np
import sys
import os

# Adicionar raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CONFIG
from utils.mesh_loader import MeshLoader

def view_mesh():
    print("="*50)
    print("VISUALIZADOR DE MALHA (PRE-TRAINING)")
    print("="*50)
    
    mesh_file = CONFIG["mesh_file"]
    print(f"Carregando malha: {mesh_file}")
    
    if not os.path.exists(mesh_file):
        print(f"❌ Arquivo não encontrado: {mesh_file}")
        return

    # Usar MeshLoader para identificar grupos físicos
    loader = MeshLoader(mesh_file)
    
    # Plotar
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # 1. Plotar Elementos (Triângulos)
    mesh = meshio.read(mesh_file)
    points = mesh.points[:, :2]
    
    if "triangle" in mesh.cells_dict:
        triangles = mesh.cells_dict["triangle"]
        ax.triplot(points[:, 0], points[:, 1], triangles, 'k-', lw=0.5, alpha=0.3, label='Malha')
    
    # 2. Plotar Nós de Contorno (Coloridos por Grupo)
    colors = ['r', 'g', 'b', 'c', 'm', 'y']
    
    print("\nGrupos Físicos Encontrados:")
    for i, name in enumerate(loader.boundary_nodes.keys()):
        pts = loader.get_boundary_points(name)
        if len(pts) > 0:
            color = colors[i % len(colors)]
            ax.plot(pts[:, 0], pts[:, 1], 'o', color=color, markersize=3, label=f"BC: {name}")
            print(f"  - {name}: {len(pts)} nós (Cor: {color})")
            
    ax.set_aspect('equal')
    ax.legend()
    ax.set_title(f"Visualização da Malha: {os.path.basename(mesh_file)}")
    ax.grid(True, alpha=0.3)
    
    # Salvar imagem em meshes/images
    base_name = os.path.basename(mesh_file).replace(".msh", "_view.png")
    output_file = os.path.join("meshes", "images", base_name)
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    plt.savefig(output_file, dpi=150)
    print(f"\n✓ Imagem salva em: {output_file}")
    # plt.show() # Não bloquear em headless

if __name__ == "__main__":
    view_mesh()
