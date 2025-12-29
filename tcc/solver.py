import numpy as np
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve

class Element:
    def __init__(self):
        self.x = self.y = self.xc = self.yc = None
        self.a = self.b = self.c = np.zeros(3)
        self.Delta = 0

    def setNodes(self, x, y):
        self.x, self.y = x, y
        self.a = [x[1] * y[2] - x[2] * y[1], x[2] * y[0] - x[0] * y[2], x[0] * y[1] - x[1] * y[0]]
        self.b = [y[1] - y[2], y[2] - y[0], y[0] - y[1]]
        self.c = [x[2] - x[1], x[0] - x[2], x[1] - x[0]]
        self.Delta = 0.5 * abs(self.b[1] * self.c[2] - self.b[2] * self.c[1])
        self.xc, self.yc = np.mean(x), np.mean(y)

class ElectrostaticElement(Element):
    def __init__(self):
        super().__init__()
        self.eps0 = 8.854187817e-12
        self.V = self.Ex = self.Ey = self.modE = None
        self.eps, self.rho = self.eps0, 0
        self.C, self.Q = np.zeros((3, 3)), np.zeros(3)
        
    def computeMatrix(self):
        fac = self.eps * self.eps0 / (4 * self.Delta)
        self.C = fac * (np.outer(self.b, self.b) + np.outer(self.c, self.c))
        self.Q = (self.rho * self.Delta / 3) * np.ones(3)

    def setNodes(self, x, y):
        super().setNodes(x, y)
        self.computeMatrix()

    def setProperties(self, eps, rho):
        self.eps, self.rho = eps*self.eps0, rho
        self.computeMatrix()

    def setNodePotentials(self, V):
        self.V = V
        self.Ex = -sum(self.b[i] * V[i] for i in range(3)) / (2 * self.Delta)
        self.Ey = -sum(self.c[i] * V[i] for i in range(3)) / (2 * self.Delta)
        self.modE = np.sqrt(self.Ex ** 2 + self.Ey ** 2)

class MagnetostaticElement(Element):
    def __init__(self):
        super().__init__()
        self.mu0 = 4 * np.pi * 1e-7
        self.nu0 = 1/(self.mu0)
        # Matrizes locais
        self.S = np.zeros((3,3))
        self.I = np.zeros(3)
        # Propriedades
        self.nu = self.nu0
        self.J = 0
        # Potenciais nodais
        self.A = None
        # Componentes do campo
        self.Bx = None
        self.By = None
        self.modB = None


    def computeMatrix(self):
        fac = self.nu*self.nu0 / (4 * self.Delta)
        self.S = fac * (np.outer(self.b, self.b) + np.outer(self.c, self.c))
        self.I = (self.J * self.Delta / 3) * np.ones(3)

    def setNodes(self, x, y):
        super().setNodes(x, y)
        self.computeMatrix()

    def setProperties(self, nu, J):
        self.nu, self.J = nu*self.nu0, J
        self.computeMatrix()

    def setNodePotentials(self, A):
        self.A = A
        self.Bx = 1 / (2 * self.Delta) * (self.c[0] * A[0] + self.c[1] * A[1] + self.c[2] * A[2])  # Calculate Bx based on A, b, and c
        self.By = -1 / (2 * self.Delta) * (self.b[0] * A[0] + self.b[1] * A[1] + self.b[2] * A[2])
        self.modB = np.sqrt(self.Bx ** 2 + self.By ** 2)  # Magnitude of B

class MagnetodynamicElement(Element):
    def __init__(self):
        super().__init__()
        self.mu0 = 4 * np.pi * 1e-7
        self.nu0 = 1/(self.mu0)
        # Matrizes locais
        self.C = np.zeros((3,3))
        self.S = np.zeros((3,3))
        self.I = np.zeros(3)
        # Propriedades
        self.nu = self.nu0
        self.sigma = 0
        self.J = 0
        # Potenciais nodais
        self.A = None
        # Componentes do campo
        self.Bx = None
        self.By = None
        self.modB = None
        self.Jind = None

    def computeMatrix(self):
        fac = self.nu * self.nu0 / (4 * self.Delta)
        self.S = fac * (np.outer(self.b, self.b) + np.outer(self.c, self.c))
        self.I = (self.J * self.Delta / 3) * np.ones(3)
        
        # Element matrix C
        for i in range(3):
            for j in range(3):
                if i == j:
                    self.C[i, j] = self.sigma * self.Delta / 6
                else:
                    self.C[i, j] = self.sigma * self.Delta / 12

    def setNodes(self, x, y):
        super().setNodes(x, y)
        self.computeMatrix()

    def setProperties(self, nu, J, sigma):
        self.nu = nu / self.mu0
        self.J = J
        self.sigma = sigma
        self.computeMatrix()

    def setNodePotentials(self, A, omega):
        self.A = A
        self.Bx = 1 / (2 * self.Delta) * (self.c[0] * A[0] + self.c[1] * A[1] + self.c[2] * A[2])  # Calculate Bx based on A, b, and c
        self.By = -1 / (2 * self.Delta) * (self.b[0] * A[0] + self.b[1] * A[1] + self.b[2] * A[2])  # Calculate By based on A, b, and c
        self.modB = np.sqrt(self.Bx ** 2 + self.By ** 2)  # Magnitude of B

        # Calculate Amed and Jind
        Amed = np.abs(np.mean(A))
        self.Jind = omega * self.sigma * Amed

class Solver:
    def __init__(self, nodes, nodeTags, triElements, elements, boundaryConditions):
        self.nodes = nodes
        self.nodeTags = nodeTags
        self.triElements = triElements
        self.elements = elements
        self.boundaryConditions = boundaryConditions
        self.numNodes = len(nodeTags)
        self.numElements = len(triElements)
        self.xc = np.zeros(self.numElements)
        self.yc = np.zeros(self.numElements)

    def apply_boundary_conditions(self):
        self.fixedNodes = []  # List to store indices of fixed nodes
        self.fixedValues = np.zeros(self.numNodes)  # Potential vector with zeros for fixed nodes

        for groupId, props in self.boundaryConditions.items():
            self.fixedNodes.extend(props['nodes'])
            self.fixedValues[props['nodes']] = props['potential']

        # Create boolean mask to identify fixed nodes
        self.isFixed = np.zeros(self.numNodes, dtype=bool)
        self.isFixed[self.fixedNodes] = True

        # Identify free (non-fixed) nodes
        self.freeNodes = np.where(~self.isFixed)[0]

    def solve(self):
        # Modify global matrix and vector to apply Dirichlet conditions
        self.globalMatrix = self.globalMatrix.tocsr()
        matrix_reduced = self.globalMatrix[self.freeNodes][:, self.freeNodes]
        vector_reduced = self.globalVector[self.freeNodes] - self.globalMatrix[self.freeNodes][:, self.fixedNodes] @ self.fixedValues[self.fixedNodes]

        # Solve for potentials at free nodes
        print(f"DEBUG: Solver - Num Nodes: {self.numNodes}")
        print(f"DEBUG: Solver - Fixed Nodes: {len(self.fixedNodes)}")
        print(f"DEBUG: Solver - Free Nodes: {len(self.freeNodes)}")
        print(f"DEBUG: Solver - Fixed Values Max: {np.max(self.fixedValues) if len(self.fixedValues)>0 else 0}")
        
        if len(self.fixedNodes) == 0:
             print("WARNING: No fixed nodes found! Solution might be non-unique or zero.")
        
        # Check Matrix
        print(f"DEBUG: Global Matrix nnz: {self.globalMatrix.nnz}")
        
        freeValues = spsolve(matrix_reduced, vector_reduced)
        
        print(f"DEBUG: Solver - Free Values Max: {np.max(np.abs(freeValues)) if len(freeValues)>0 else 0}")

        # Construct the complete potential vector in the correct order (same order as nodeTags)
        self.potential[self.fixedNodes] = self.fixedValues[self.fixedNodes]
        self.potential[self.freeNodes] = freeValues

class ElectrostaticSolver(Solver):
    def __init__(self, nodes, nodeTags, triElements, elements, boundaryConditions):
        super().__init__(nodes, nodeTags, triElements, elements, boundaryConditions)
        self.globalMatrix = lil_matrix((self.numNodes, self.numNodes))
        self.globalVector = np.zeros(self.numNodes)
        self.potential = np.zeros(self.numNodes)
        self.Ex = np.zeros(self.numElements)
        self.Ey = np.zeros(self.numElements)
        self.modE = np.zeros(self.numElements)
        self.rho = np.zeros(self.numElements)

    def assemble_global_matrix_and_vector(self):
        for e, nodeIndices in enumerate(self.triElements):
            for iLocal, iGlobal in enumerate(nodeIndices):
                self.globalVector[iGlobal] += self.elements[e].Q[iLocal]
                for jLocal, jGlobal in enumerate(nodeIndices):
                    self.globalMatrix[iGlobal, jGlobal] += self.elements[e].C[iLocal, jLocal]

    def calculate_electric_field(self):
        for i, nodeIndices in enumerate(self.triElements):
            V_elem = self.potential[nodeIndices]
            self.elements[i].setNodePotentials(V_elem)
            self.Ex[i], self.Ey[i], self.modE[i] = self.elements[i].Ex, self.elements[i].Ey, self.elements[i].modE
            self.xc[i], self.yc[i] = self.elements[i].xc, self.elements[i].yc

    def get_potential(self):
        return self.potential

    def get_electric_field(self):
        return self.Ex, self.Ey, self.modE, self.xc, self.yc

class MagnetostaticSolver(Solver):
    def __init__(self, nodes, nodeTags, triElements, elements, boundaryConditions):
        super().__init__(nodes, nodeTags, triElements, elements, boundaryConditions)
        self.globalMatrix = lil_matrix((self.numNodes, self.numNodes))
        self.globalVector = np.zeros(self.numNodes)
        self.potential = np.zeros(self.numNodes)
        self.Bx = np.zeros(self.numElements)
        self.By = np.zeros(self.numElements)
        self.modB = np.zeros(self.numElements)

    def assemble_global_matrix_and_vector(self):
        for e, nodeIndices in enumerate(self.triElements):
            for iLocal, iGlobal in enumerate(nodeIndices):
                self.globalVector[iGlobal] += self.elements[e].I[iLocal]
                for jLocal, jGlobal in enumerate(nodeIndices):
                    self.globalMatrix[iGlobal, jGlobal] += self.elements[e].S[iLocal, jLocal]

    def calculate_magnetic_field(self):
        for i, nodeIndices in enumerate(self.triElements):
            A_elem = self.potential[nodeIndices]
            self.elements[i].setNodePotentials(A_elem)
            self.Bx[i], self.By[i], self.modB[i] = self.elements[i].Bx, self.elements[i].By, self.elements[i].modB
            self.xc[i], self.yc[i] = self.elements[i].xc, self.elements[i].yc

    def get_potential(self):
        return self.potential

    def get_magnetic_field(self):
        return self.Bx, self.By, self.modB, self.xc, self.yc
 
class MagnetodynamicSolver(Solver):
    def __init__(self, nodes, nodeTags, triElements, elements, boundaryConditions, frequency):
        super().__init__(nodes, nodeTags, triElements, elements, boundaryConditions)
        self.globalMatrix = lil_matrix((self.numNodes, self.numNodes), dtype='complex')
        self.globalVector = np.zeros(self.numNodes, dtype='complex')
        self.potential = np.zeros(self.numNodes, dtype='complex')
        self.Bx = np.zeros(self.numElements, dtype='complex')
        self.By = np.zeros(self.numElements, dtype='complex')
        self.modB = np.zeros(self.numElements, dtype='complex')
        self.Jind = np.zeros(self.numElements, dtype='complex')
        self.frequency = frequency

    def assemble_global_matrix_and_vector(self):
        f = self.frequency
        for e, nodeIndices in enumerate(self.triElements):
            element = self.elements[e]
            for iLocal, iGlobal in enumerate(nodeIndices):
                self.globalVector[iGlobal] += element.I[iLocal]
                for jLocal, jGlobal in enumerate(nodeIndices):
                    self.globalMatrix[iGlobal, jGlobal] += complex(element.S[iLocal, jLocal], 2 * np.pi * f * element.C[iLocal, jLocal])

    def calculate_Jind(self):
        for e, element in enumerate(self.elements):
            self.Jind[e] = element.Jind

    def calculate_magnetic_field(self):
        for i, nodeIndices in enumerate(self.triElements):
            A_elem = self.potential[nodeIndices]
            self.elements[i].setNodePotentials(A_elem, self.frequency)
            self.Bx[i], self.By[i], self.modB[i] = self.elements[i].Bx, self.elements[i].By, self.elements[i].modB
            self.xc[i], self.yc[i] = self.elements[i].xc, self.elements[i].yc

    def get_potential(self):
        return self.potential

    def get_Jind(self):
        self.calculate_Jind()
        return self.Jind

    def get_magnetic_field(self):
        return self.Bx, self.By, self.modB, self.xc, self.yc