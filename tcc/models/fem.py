import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from scipy.interpolate import RegularGridInterpolator

class PoissonFEM:
    def __init__(self, problem, Nx=50, Ny=50):
        """
        Solver FEM para equação de Poisson 2D: -Laplacian(u) = f
        no domínio [0,1]x[0,1] com condições de Dirichlet.
        
        Args:
            problem (dict): Dicionário do problema contendo 'u_true' (para BCs) e 'f' (opcional).
                            Se 'f' não for dado, tentamos inferir ou usar u_true.
            Nx, Ny (int): Número de elementos nas direções x e y.
        """
        self.problem = problem
        self.Nx = Nx
        self.Ny = Ny
        
        # Malha
        self.x = np.linspace(0, 1, Nx + 1)
        self.y = np.linspace(0, 1, Ny + 1)
        self.dx = 1.0 / Nx
        self.dy = 1.0 / Ny
        self.n_nodes = (Nx + 1) * (Ny + 1)
        
        # Mapeamento (i, j) -> k (índice global)
        self.idx = lambda i, j: i * (Ny + 1) + j
        
        self.u_fem = None
        self.interpolator = None

    def _local_stiffness(self):
        """
        Matriz de rigidez local para elemento retangular bilinear (Q1).
        Tamanho 4x4.
        """
        # Razão de aspecto
        r = self.dx / self.dy
        
        # Integrais pré-calculadas para -Laplacian em elemento retangular
        # K_local = integral(grad(phi_i) . grad(phi_j))
        
        # Contribuição dx (dphi/dx * dphi/dx)
        # Fator dy/dx = 1/r
        Kx = (1.0 / r) * np.array([
            [ 2, -2,  1, -1], # 0-1, 0-2, 0-3? Ordem: (0,0), (1,0), (1,1), (0,1)
            [-2,  2, -1,  1],
            [ 1, -1,  2, -2],
            [-1,  1, -2,  2]
        ]) / 6.0
        
        # Contribuição dy (dphi/dy * dphi/dy)
        # Fator dx/dy = r
        Ky = r * np.array([
            [ 2,  1, -1, -2],
            [ 1,  2, -2, -1],
            [-1, -2,  2,  1],
            [-2, -1,  1,  2]
        ]) / 6.0
        
        return Kx + Ky

    def solve(self):
        """Monta e resolve o sistema linear Ku = F."""
        print(f"FEM: Montando sistema {self.n_nodes}x{self.n_nodes}...")
        
        # Matriz Global (COO format para construção rápida)
        rows = []
        cols = []
        data = []
        
        # Vetor de Carga
        F = np.zeros(self.n_nodes)
        
        # Matriz local
        Ke = self._local_stiffness()
        
        # Função fonte f(x,y)
        # Poisson: -Laplacian(u) = f
        # Se u_true = sin(pi*x)*sin(pi*y)
        # f = 2*pi^2 * sin(pi*x)*sin(pi*y)
        def source_term(x, y):
            return 2.0 * (np.pi**2) * np.sin(np.pi * x) * np.sin(np.pi * y)

        # Assembly
        for i in range(self.Nx):
            for j in range(self.Ny):
                # Nós do elemento (sentido anti-horário partindo de (i,j))
                # 3 -- 2
                # |    |
                # 0 -- 1
                n0 = self.idx(i, j)
                n1 = self.idx(i + 1, j)
                n2 = self.idx(i + 1, j + 1)
                n3 = self.idx(i, j + 1)
                nodes = [n0, n1, n2, n3]
                
                # Montagem da Matriz K
                for r in range(4):
                    for c in range(4):
                        rows.append(nodes[r])
                        cols.append(nodes[c])
                        data.append(Ke[r, c])
                
                # Montagem do Vetor F (Integração numérica simples no centro do elemento)
                xc = self.x[i] + self.dx/2
                yc = self.y[j] + self.dy/2
                f_val = source_term(xc, yc)
                
                # Distribui carga igualmente para os 4 nós (lumped)
                # Integral(f * phi) approx f_center * Area / 4
                load = f_val * (self.dx * self.dy) / 4.0
                for n in nodes:
                    F[n] += load

        K = sp.coo_matrix((data, (rows, cols)), shape=(self.n_nodes, self.n_nodes)).tocsr()
        
        # Condições de Contorno (Dirichlet)
        # Identificar nós da borda
        boundary_nodes = []
        for i in range(self.Nx + 1):
            for j in range(self.Ny + 1):
                if i == 0 or i == self.Nx or j == 0 or j == self.Ny:
                    boundary_nodes.append(self.idx(i, j))
        
        # Aplicar BCs: Modificar K e F
        # Método da penalidade ou substituição de linha (aqui: substituição 1 na diag)
        # Para matrizes grandes, zerar linhas é lento. Vamos usar uma abordagem de setar valor.
        
        # Maneira eficiente para CSR:
        # 1. Encontrar linhas de borda
        # 2. Zerar essas linhas
        # 3. Colocar 1 na diagonal
        # 4. Colocar valor do BC em F
        
        # Nota: Implementação simplificada "Lil" para facilidade de modificação, depois converte
        K = K.tolil()
        u_true = self.problem["u_true"]
        
        for node in boundary_nodes:
            # Recupera coordenadas
            # node = i * (Ny+1) + j
            i = node // (self.Ny + 1)
            j = node % (self.Ny + 1)
            xi, yj = self.x[i], self.y[j]
            
            # Valor prescrito
            val = u_true(np.array([[xi, yj]])).item()
            
            # Modifica sistema
            K.rows[node] = [node]
            K.data[node] = [1.0]
            F[node] = val
            
        K = K.tocsr()
        
        print("FEM: Resolvendo sistema linear...")
        self.u_fem = spla.spsolve(K, F)
        
        # Criar interpolador para predict
        # Reshape para (Nx+1, Ny+1) -> cuidado com a ordem dos eixos no meshgrid vs array
        # idx = i * (Ny+1) + j  => i é linha (x), j é coluna (y)
        # Grid data deve ser (x, y)
        grid_data = self.u_fem.reshape((self.Nx + 1, self.Ny + 1))
        self.interpolator = RegularGridInterpolator((self.x, self.y), grid_data, bounds_error=False, fill_value=None)
        print("FEM: Solução concluída.")

    def predict(self, X):
        """
        Interpola a solução FEM nos pontos X.
        X: (N, 2) array
        """
        if self.interpolator is None:
            raise RuntimeError("Modelo FEM não resolvido. Chame solve() primeiro.")
        return self.interpolator(X)
