import gmsh
import sys
import os

def generate_lshape_mesh(filename="meshes/lshape.msh", lc=0.05):
    """
    Gera uma malha em forma de L: [-1,1]x[-1,1] menos [0,1]x[0,1].
    Canto reentrante em (0,0).
    """
    gmsh.initialize()
    gmsh.model.add("L_Shape")

    # Pontos
    # 1: (-1, -1)
    # 2: (1, -1)
    # 3: (1, 0)
    # 4: (0, 0) -> Canto Reentrante (Singularidade)
    # 5: (0, 1)
    # 6: (-1, 1)
    
    p1 = gmsh.model.geo.addPoint(-1, -1, 0, lc)
    p2 = gmsh.model.geo.addPoint( 1, -1, 0, lc)
    p3 = gmsh.model.geo.addPoint( 1,  0, 0, lc)
    p4 = gmsh.model.geo.addPoint( 0,  0, 0, lc/5) # Refinamento no canto reentrante
    p5 = gmsh.model.geo.addPoint( 0,  1, 0, lc)
    p6 = gmsh.model.geo.addPoint(-1,  1, 0, lc)

    # Linhas
    l1 = gmsh.model.geo.addLine(p1, p2) # Bottom
    l2 = gmsh.model.geo.addLine(p2, p3) # Right Lower
    l3 = gmsh.model.geo.addLine(p3, p4) # Inner Horizontal
    l4 = gmsh.model.geo.addLine(p4, p5) # Inner Vertical
    l5 = gmsh.model.geo.addLine(p5, p6) # Top
    l6 = gmsh.model.geo.addLine(p6, p1) # Left

    # Loop e Superfície
    cl = gmsh.model.geo.addCurveLoop([l1, l2, l3, l4, l5, l6])
    s1 = gmsh.model.geo.addPlaneSurface([cl])

    gmsh.model.geo.synchronize()

    # Grupos Físicos (Boundary Conditions)
    # Vamos definir potenciais diferentes para criar um campo interessante
    gmsh.model.addPhysicalGroup(1, [l5], name="Top")    # 100V
    gmsh.model.addPhysicalGroup(1, [l1], name="Bottom") # 0V
    gmsh.model.addPhysicalGroup(1, [l6], name="Left")   # 0V
    gmsh.model.addPhysicalGroup(1, [l2], name="Right")  # 0V
    
    # As bordas internas (l3, l4) perto da singularidade
    gmsh.model.addPhysicalGroup(1, [l3, l4], name="Inner") # 0V ou Neumann? Vamos por 0V para forçar gradiente alto

    gmsh.model.addPhysicalGroup(2, [s1], name="Domain")

    # Gerar Malha
    gmsh.model.mesh.generate(2)
    
    # Criar diretório se não existir
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    gmsh.write(filename)
    print(f"✓ Malha gerada em: {filename}")
    
    gmsh.finalize()

if __name__ == "__main__":
    generate_lshape_mesh()
