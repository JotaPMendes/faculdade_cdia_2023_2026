import numpy as np

def generate_data_for_ml(problem, cfg, model_fem=None):
    """Gera dados de treino (dentro do domínio) e teste (extrapolação)."""
    kind = problem["kind"]
    u_true = problem.get("u_true")
    
    # Se não houver solução analítica, tentamos usar o FEM como Ground Truth
    if u_true is None:
        if model_fem is not None:
            print("ℹ️ 'u_true' não definido. Usando solução FEM como Ground Truth.")
            u_true = lambda x: model_fem.predict(x)
        else:
            print("⚠️ Aviso: 'u_true' não definido e 'model_fem' não fornecido. Pulando geração de dados para ML Clássico.")
            return np.empty((0,2)), np.empty((0,)), np.empty((0,2)), np.empty((0,))
    
    if kind == "time":
        # Treino: t <= T_train
        N = cfg["N_data"]
        Xtr = np.random.rand(N, 2)
        Xtr[:,0] *= cfg["Lx"]
        Xtr[:,1] *= cfg["T_train"]
        ytr = u_true(Xtr)

        # Teste: Extrapolação Temporal (T_train < t < T_eval)
        Nte = N // 2
        Xte = np.random.rand(Nte, 2)
        Xte[:,0] *= cfg["Lx"]
        Xte[:,1] = cfg["T_train"] + np.random.rand(Nte)*(cfg["T_eval"] - cfg["T_train"])
        yte = u_true(Xte)
        
        return Xtr, ytr, Xte, yte

    elif kind == "space":
        # Treino: Dentro do train_box
        bx0, by0, bx1, by1 = cfg["train_box"]
        Nx, Ny = cfg["Nx_train"], cfg["Ny_train"]
        
        xs = np.linspace(bx0, bx1, Nx)
        ys = np.linspace(by0, by1, Ny)
        Xtr = np.stack(np.meshgrid(xs, ys), -1).reshape(-1, 2)
        ytr = u_true(Xtr)
        
        # Teste: Fora do train_box (Generalização Espacial)
        # Geramos pontos em todo o domínio [0,1]x[0,1] e filtramos o que NÃO está no box
        N_cand = 10000
        Xcand = np.random.rand(N_cand, 2)
        mask_in_box = (
            (Xcand[:,0] >= bx0) & (Xcand[:,0] <= bx1) &
            (Xcand[:,1] >= by0) & (Xcand[:,1] <= by1)
        )
        Xte = Xcand[~mask_in_box] # Apenas fora
        yte = u_true(Xte)
        
        return Xtr, ytr, Xte, yte

    elif kind == "electrostatic":
        # Para eletrostática (malha arbitrária), usamos bounding box do config ou amostragem aleatória no domínio
        
        bx0, by0, bx1, by1 = cfg["train_box"]
        N = cfg["N_data"]
        
        # Treino: Pontos aleatórios dentro do box
        Xtr = np.random.rand(N, 2)
        Xtr[:,0] = bx0 + Xtr[:,0] * (bx1 - bx0)
        Xtr[:,1] = by0 + Xtr[:,1] * (by1 - by0)
        ytr = u_true(Xtr)
        
        # Teste: Pontos aleatórios fora do box (mas dentro do domínio global [0,1]x[0,1] aproximado?)
        N_cand = 20000
        # Assumindo domínio aprox [0,1]x[0,1] baseado no .msh
        Xcand = np.random.rand(N_cand, 2) 
        
        # Filtrar fora do box de treino
        mask_in_box = (
            (Xcand[:,0] >= bx0) & (Xcand[:,0] <= bx1) &
            (Xcand[:,1] >= by0) & (Xcand[:,1] <= by1)
        )
        Xcand = Xcand[~mask_in_box]
        
        ycand = u_true(Xcand)
        # Filtrar NaNs (fora da malha)
        mask_valid = ~np.isnan(ycand)
        Xte = Xcand[mask_valid]
        yte = ycand[mask_valid]
        
        # Limitar tamanho de teste
        if len(Xte) > N // 2:
            Xte = Xte[:N//2]
            yte = yte[:N//2]
            
        return Xtr, ytr, Xte, yte

    else:
        # Fallback
        return np.empty((0,2)), np.empty((0,)), np.empty((0,2)), np.empty((0,))