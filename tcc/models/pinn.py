import os
import deepxde as dde
from utils.checkpoint import CheckpointManager

def train_pinn(problem, config):
    data, net = problem["data"], problem["net"]
    model = dde.Model(data, net)
    
    # Obter configurações específicas do problema (se existirem)
    pinn_cfg = problem.get("pinn_config", {})
    
    # Pesos dinâmicos baseados no número de constraints
    # Ex: Heat -> 4 perdas (1 PDE + 2 BCs + 1 IC)
    num_losses = len(data.bcs) + (1 if data.pde is not None else 0)
    loss_weights = [1.0] * num_losses

    # Otimizador Adam
    model.compile("adam", lr=1e-3, loss_weights=loss_weights)
    
    # Configuração de Checkpoint via Manager
    # Se keep_checkpoints for 0 ou None, o Manager trata como infinito
    max_keep = config.get("keep_checkpoints", 0)
    ckpt_manager = CheckpointManager(max_keep=max_keep)
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
    
    # Early Stopping
    early_stopping = dde.callbacks.EarlyStopping(min_delta=1e-4, patience=2000)
    
    # Frequência de Checkpoint
    save_period = config.get("checkpoint_every", 1000)
    checker = dde.callbacks.ModelCheckpoint(ckpt_path, save_better_only=True, period=save_period)
    
    # Tentar restaurar modelo existente
    latest_step = 0
    restore_path = None
    
    if os.path.exists(ckpt_dir):
        checkpoints = [f for f in os.listdir(ckpt_dir) if f.startswith("model.ckpt-") and f.endswith(".index")]
        if checkpoints:
            steps = [int(f.split("-")[1].split(".")[0]) for f in checkpoints]
            latest_step = max(steps)
            restore_path = os.path.join(ckpt_dir, f"model.ckpt-{latest_step}.ckpt")
            print(f">>> Checkpoint encontrado: {restore_path} (Step {latest_step})")
            model.restore(restore_path)
            model.train_state.step = latest_step
    
    # Treinamento Adam
    # Prioridade: 1. pinn_config (do problema), 2. config (global), 3. Default
    total_adam_iters = pinn_cfg.get("train_steps_adam", config.get("train_steps_adam", 15000))
    remaining_iters = total_adam_iters - latest_step
    
    if remaining_iters > 0:
        print(f">>> Iniciando treinamento ADAM por {remaining_iters} iterações (Total: {total_adam_iters})...")
        resampler = dde.callbacks.PDEPointResampler(period=1000)
        model.train(iterations=remaining_iters, callbacks=[resampler, checker, cleanup_cb, early_stopping], display_every=500)
    else:
        print(f">>> Treinamento ADAM já concluído (Step {latest_step} >= {total_adam_iters}). Pulando...")

    # Refinamento L-BFGS
    lbfgs_iters = pinn_cfg.get("train_steps_lbfgs", config.get("train_steps_lbfgs", 5000))
    if lbfgs_iters > 0:
        print(f">>> Refinando com L-BFGS por {lbfgs_iters} iterações...")
        model.compile("L-BFGS", loss_weights=loss_weights)
        model.train(iterations=lbfgs_iters, callbacks=[checker, cleanup_cb, early_stopping], display_every=500)
    
    return model