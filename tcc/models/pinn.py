import os
import deepxde as dde
from utils.checkpoint import CheckpointManager

def train_pinn(problem, config):
    data, net = problem["data"], problem["net"]
    model = dde.Model(data, net)
    
    # Pesos dinâmicos baseados no número de constraints
    # Ex: Heat -> 4 perdas (1 PDE + 2 BCs + 1 IC)
    num_losses = len(data.bcs) + (1 if data.pde is not None else 0)
    loss_weights = [1.0] * num_losses

    # Otimizador Adam
    model.compile("adam", lr=1e-3, loss_weights=loss_weights)
    
    # Configuração de Checkpoint via Manager
    ckpt_manager = CheckpointManager(max_keep=3)
    ckpt_dir = ckpt_manager.get_run_dir(config)
    ckpt_path = os.path.join(ckpt_dir, "model.ckpt")
    
    # Callback customizado para limpeza
    class CleanupCallback(dde.callbacks.Callback):
        def __init__(self, manager, run_dir):
            super().__init__()
            self.manager = manager
            self.run_dir = run_dir
            
        def on_epoch_end(self):
            pass
            
        def on_train_end(self):
            self.manager.cleanup(self.run_dir)
            
    cleanup_cb = CleanupCallback(ckpt_manager, ckpt_dir)
        
    checker = dde.callbacks.ModelCheckpoint(ckpt_path, save_better_only=True, period=1000)
    resampler = dde.callbacks.PDEPointResampler(period=100)

    # Tentar restaurar modelo existente
    # DeepXDE salva como model.ckpt-STEP.ckpt.index, etc.
    # Vamos procurar o arquivo de checkpoint mais recente
    latest_step = 0
    restore_path = None
    
    # Verifica se existe algum checkpoint
    if os.path.exists(ckpt_dir):
        # Lista arquivos que começam com model.ckpt-
        checkpoints = [f for f in os.listdir(ckpt_dir) if f.startswith("model.ckpt-") and f.endswith(".index")]
        if checkpoints:
            # Extrai o passo de cada checkpoint (ex: model.ckpt-1000.index -> 1000)
            steps = [int(f.split("-")[1].split(".")[0]) for f in checkpoints]
            latest_step = max(steps)
            restore_path = os.path.join(ckpt_dir, f"model.ckpt-{latest_step}.ckpt")
            print(f">>> Checkpoint encontrado: {restore_path} (Step {latest_step})")
            model.restore(restore_path)
            model.train_state.step = latest_step
    
    # Treinamento Adam
    total_adam_iters = 15000
    remaining_iters = total_adam_iters - latest_step
    
    if remaining_iters > 0:
        print(f">>> Iniciando treinamento ADAM por {remaining_iters} iterações (Total: {total_adam_iters})...")
        model.train(iterations=remaining_iters, callbacks=[resampler, checker, cleanup_cb], display_every=1000)
    else:
        print(f">>> Treinamento ADAM já concluído (Step {latest_step} >= {total_adam_iters}). Pulando...")

    # Refinamento L-BFGS
    print(">>> Refinando com L-BFGS...")
    model.compile("L-BFGS", loss_weights=loss_weights)
    model.train(iterations=5000, callbacks=[checker, cleanup_cb])
    
    return model