import gmsh
import sys
import os
import numpy as np

def generate_stator_mesh(filename="meshes/files/stator.msh", r_in=0.5, r_out=1.0, n_slots=12, slot_depth=0.2, slot_width_ratio=0.5):
    """
    Gera uma malha de estator de motor simplificada.
    """
    gmsh.initialize()
    gmsh.model.add("stator")

    # Parâmetros geométricos
    lc = 0.02  # REFINADO: 0.05 -> 0.02 para mais pontos de treino

    # 1. Disco Externo (Estator completo)
    disk_out = gmsh.model.occ.addDisk(0, 0, 0, r_out, r_out)
    
    # 2. Disco Interno (Furo do Rotor)
    disk_in = gmsh.model.occ.addDisk(0, 0, 0, r_in, r_in)
    
    # 3. Criar Slots
    slots = []
    angle_step = 2 * np.pi / n_slots
    slot_w = (2 * np.pi * r_in / n_slots) * slot_width_ratio
    
    for i in range(n_slots):
        angle = i * angle_step
        w = slot_w
        h = slot_depth + 0.1
        sid = gmsh.model.occ.addRectangle(r_in - 0.05, -w/2, 0, h, w)
        gmsh.model.occ.rotate([(2, sid)], 0, 0, 0, 0, 0, 1, angle)
        slots.append((2, sid))

    # Operações Booleanas
    ring = gmsh.model.occ.cut([(2, disk_out)], [(2, disk_in)])
    final_shape = gmsh.model.occ.cut(ring[0], slots)
    
    gmsh.model.occ.synchronize()

    # Definir Grupos Físicos
    lines = gmsh.model.getEntities(dim=1)
    outer_lines = []
    inner_lines = []
    
    for line in lines:
        tag = line[1]
        bbox = gmsh.model.getBoundingBox(1, tag)
        rmin = np.sqrt(bbox[0]**2 + bbox[1]**2)
        rmax = np.sqrt(bbox[3]**2 + bbox[4]**2)
        r_avg = (rmin + rmax) / 2
        
        if r_avg > r_out - 0.01:
            outer_lines.append(tag)
        else:
            inner_lines.append(tag)
            
    gmsh.model.addPhysicalGroup(1, outer_lines, name="Outer")
    gmsh.model.addPhysicalGroup(1, inner_lines, name="Inner")
    
    surfaces = gmsh.model.getEntities(dim=2)
    gmsh.model.addPhysicalGroup(2, [s[1] for s in surfaces], name="Domain")

    # Definir tamanho da malha global
    gmsh.model.mesh.setSize(gmsh.model.getEntities(0), lc)

    # Gerar Malha
    gmsh.model.mesh.generate(2)
    
    # Salvar
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    gmsh.write(filename)
    gmsh.finalize()
    print(f"✓ Malha de estator gerada em: {filename}")

if __name__ == "__main__":
    generate_stator_mesh()
