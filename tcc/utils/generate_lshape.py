import gmsh
import sys

def generate_lshape(filename="meshes/files/lshape.msh", lc=0.05):
    gmsh.initialize()
    gmsh.model.add("lshape")

    # Pontos
    p1 = gmsh.model.geo.addPoint(0, 0, 0, lc)
    p2 = gmsh.model.geo.addPoint(1, 0, 0, lc)
    p3 = gmsh.model.geo.addPoint(1, 0.5, 0, lc)
    p4 = gmsh.model.geo.addPoint(0.5, 0.5, 0, lc)
    p5 = gmsh.model.geo.addPoint(0.5, 1, 0, lc)
    p6 = gmsh.model.geo.addPoint(0, 1, 0, lc)

    # Linhas
    l1 = gmsh.model.geo.addLine(p1, p2)
    l2 = gmsh.model.geo.addLine(p2, p3)
    l3 = gmsh.model.geo.addLine(p3, p4)
    l4 = gmsh.model.geo.addLine(p4, p5)
    l5 = gmsh.model.geo.addLine(p5, p6)
    l6 = gmsh.model.geo.addLine(p6, p1)

    # Loop e Superfície
    cl = gmsh.model.geo.addCurveLoop([l1, l2, l3, l4, l5, l6])
    s = gmsh.model.geo.addPlaneSurface([cl])

    gmsh.model.geo.synchronize()

    # Grupos Físicos
    gmsh.model.addPhysicalGroup(1, [l1, l2, l3, l4, l5, l6], 1, name="Boundary")
    gmsh.model.addPhysicalGroup(2, [s], 1, name="Domain")

    gmsh.model.mesh.generate(2)
    gmsh.write(filename)
    gmsh.finalize()
    print(f"Mesh saved to {filename}")

if __name__ == "__main__":
    generate_lshape()
