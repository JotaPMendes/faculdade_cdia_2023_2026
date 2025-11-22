import os
import deepxde as dde

def train_pinn(problem):
    data, net = problem["data"], problem["net"]
    model = dde.Model(data, net)
    
    # Pesos dinâmicos baseados no número de constraints
    # Ex: Heat -> 4 perdas (1 PDE + 2 BCs + 1 IC)
    num_losses = len(data.bc) + (1 if data.pde is not None else 0)
    loss_weights = [1.0] * num_losses

    # Otimizador Adam
    model.compile("adam", lr=1e-3, loss_weights=loss_weights)
    
    # Callbacks: Resampling mais frequente e Salvamento
    if not os.path.exists("checkpoints"): os.makedirs("checkpoints")
    checker = dde.callbacks.ModelCheckpoint("checkpoints/model.ckpt", save_better_only=True, period=1000)
    resampler = dde.callbacks.PDEPointResampler(period=100) # Resample a cada 100 épocas
    
    print(">>> Iniciando treinamento ADAM...")
    model.train(iterations=15000, callbacks=[resampler, checker], display_every=1000)
    
    # Refinamento L-BFGS
    print(">>> Refinando com L-BFGS...")
    model.compile("L-BFGS", loss_weights=loss_weights)
    model.train(iterations=5000, callbacks=[checker]) # Resampler não funciona bem com LBFGS
    
    # Recarrega o melhor modelo
    # model.restore("checkpoints/model.ckpt-" + str(model.train_state.best_step))
    return model