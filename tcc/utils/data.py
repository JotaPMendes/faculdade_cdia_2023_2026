import numpy as np

def generate_data_for_ml(problem, cfg):
    """Gera dados de treino (dentro do domínio) e teste (extrapolação)."""
    kind = problem["kind"]
    u_true = problem["u_true"]
    
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