import gmsh
import sys
import os
import random

def generate_plate_holes(filename="meshes/files/plate_holes.msh", L=1.0, n_holes=5, min_r=0.05, max_r=0.1):
    gmsh.initialize()
    gmsh.model.add("plate_holes")

    # 1. Criar Placa Base (Retângulo)
    # Ponto inferior esquerdo (0,0)
    # Tag 1
    plate = gmsh.model.occ.addRectangle(0, 0, 0, L, L)

    # 2. Criar Furos (Discos)
    holes = []
    
    # Grid de segurança para evitar sobreposição
    # Vamos dividir em células e colocar um furo em algumas delas
    cells = []
    grid_size = int(n_holes**0.5) + 1
    step = L / grid_size
    
    for i in range(grid_size):
        for j in range(grid_size):
            cx = (i + 0.5) * step
            cy = (j + 0.5) * step
            cells.append((cx, cy))
            
    random.shuffle(cells)
    
    for k in range(min(n_holes, len(cells))):
        cx, cy = cells[k]
        # Randomizar levemente a posição dentro da célula
        jitter = step * 0.2
        cx += random.uniform(-jitter, jitter)
        cy += random.uniform(-jitter, jitter)
        
        r = random.uniform(min_r, max_r)
        
        # Garantir que não toque as bordas
        if cx - r < 0: cx = r + 0.01
        if cx + r > L: cx = L - r - 0.01
        if cy - r < 0: cy = r + 0.01
        if cy + r > L: cy = L - r - 0.01
        
        hole = gmsh.model.occ.addDisk(cx, cy, 0, r, r)
        holes.append(hole)

    # 3. Subtrair Furos da Placa
    # cut retorna (dim, tag)
    # plate é (2, tag)
    domain = gmsh.model.occ.cut([(2, plate)], [(2, h) for h in holes])
    
    gmsh.model.occ.synchronize()

    # 4. Grupos Físicos (Boundary Conditions)
    # Precisamos identificar as linhas
    # Left: x=0, Right: x=L, Top: y=L, Bottom: y=0
    # Holes: O resto
    
    lines = gmsh.model.getEntities(dim=1)
    
    left_lines = []
    right_lines = []
    top_lines = []
    bottom_lines = []
    hole_lines = []
    
    for line in lines:
        tag = line[1]
        bbox = gmsh.model.getBoundingBox(1, tag)
        # bbox: minx, miny, minz, maxx, maxy, maxz
        
        # Tolerância
        tol = 1e-3
        
        is_left = abs(bbox[0] - 0) < tol and abs(bbox[3] - 0) < tol
        is_right = abs(bbox[0] - L) < tol and abs(bbox[3] - L) < tol
        is_bottom = abs(bbox[1] - 0) < tol and abs(bbox[4] - 0) < tol
        is_top = abs(bbox[1] - L) < tol and abs(bbox[4] - L) < tol
        
        if is_left:
            left_lines.append(tag)
        elif is_right:
            right_lines.append(tag)
        elif is_bottom:
            bottom_lines.append(tag)
        elif is_top:
            top_lines.append(tag)
        else:
            hole_lines.append(tag)

    gmsh.model.addPhysicalGroup(1, left_lines, name="Left")
    gmsh.model.addPhysicalGroup(1, right_lines, name="Right")
    gmsh.model.addPhysicalGroup(1, top_lines, name="Top")
    gmsh.model.addPhysicalGroup(1, bottom_lines, name="Bottom")
    gmsh.model.addPhysicalGroup(1, hole_lines, name="Holes")
    
    # Superfície Física (Domínio)
    surfaces = [d[1] for d in domain[0]]
    gmsh.model.addPhysicalGroup(2, surfaces, name="Domain")

    # 5. Gerar Malha
    gmsh.option.setNumber("Mesh.MeshSizeMax", 0.03) # Resolução fina
    gmsh.option.setNumber("Mesh.MeshSizeMin", 0.01)
    
    gmsh.model.mesh.generate(2)
    
    # Salvar
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    gmsh.write(filename)
    print(f"✓ Malha gerada em: {filename}")
    
    gmsh.finalize()

if __name__ == "__main__":
    generate_plate_holes()
