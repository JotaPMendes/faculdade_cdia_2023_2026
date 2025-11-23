import numpy as np
import os
import meshio

class MeshLoader:
    def __init__(self, filename):
        # Resolve path: check if absolute, else check in meshes/, else use as is
        if os.path.isabs(filename):
            self.filename = filename
        else:
            # Try meshes/ directory first
            meshes_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "meshes", filename)
            if os.path.exists(meshes_path):
                self.filename = meshes_path
            else:
                self.filename = filename
                
        self.nodes = {} # id -> [x, y, z] (Not strictly used as dict anymore, but kept for compatibility if needed)
        self.points = None # (N, 3) array
        self.physical_names = {} # tag -> name
        self.boundary_nodes = {} # name -> list of node indices (0-indexed)
        self.domain_nodes = [] # list of node indices inside domain
        
        self._load_mesh()

    def _load_mesh(self):
        if not os.path.exists(self.filename):
            raise FileNotFoundError(f"Mesh file not found: {self.filename}")
            
        mesh = meshio.read(self.filename)
        self.points = mesh.points
        
        # Parse physical names
        # mesh.field_data maps Name -> [tag, dim]
        tag_to_name = {}
        for name, data in mesh.field_data.items():
            tag = data[0]
            tag_to_name[tag] = name
            self.physical_names[tag] = name
            
        # Process cells
        # mesh.cells_dict['line'] -> (M, 2)
        # mesh.cell_data['gmsh:physical'] -> list of arrays corresponding to cells
        
        # We need to match cell blocks to cell data
        # meshio stores cells as a list of blocks, and cell_data as a dict of lists
        
        # Iterate over blocks to find lines and triangles
        cell_data_physical = mesh.cell_data.get('gmsh:physical', [])
        
        for i, cell_block in enumerate(mesh.cells):
            cell_type = cell_block.type
            data = cell_block.data # (N_cells, N_nodes_per_cell)
            
            # Get physical tags for this block
            if i < len(cell_data_physical):
                tags = cell_data_physical[i]
            else:
                tags = []
            
            if cell_type == 'line':
                # Boundary elements
                for j, tag in enumerate(tags):
                    if tag in tag_to_name:
                        name = tag_to_name[tag]
                        if name not in self.boundary_nodes:
                            self.boundary_nodes[name] = set()
                        
                        # Add nodes to boundary set
                        for node_idx in data[j]:
                            self.boundary_nodes[name].add(node_idx)
                            
            elif cell_type == 'triangle':
                # Domain elements
                domain_set = set(self.domain_nodes)
                for cell in data:
                    for node_idx in cell:
                        domain_set.add(node_idx)
                self.domain_nodes = list(domain_set)

    def get_boundary_points(self, boundary_name):
        """Returns (N, 2) array of points for a given boundary name."""
        if boundary_name not in self.boundary_nodes:
            return np.empty((0, 2))
        
        node_indices = list(self.boundary_nodes[boundary_name])
        # self.points is (N, 3), take (N, 2)
        return self.points[node_indices, :2]

    def get_domain_points(self):
        """Returns (N, 2) array of all points in the domain."""
        if not self.domain_nodes:
            # If no domain nodes identified (e.g. only points loaded), return all
            return self.points[:, :2]
            
        return self.points[self.domain_nodes, :2]

    def get_all_points(self):
        """Returns (N, 2) array of ALL nodes."""
        return self.points[:, :2]
