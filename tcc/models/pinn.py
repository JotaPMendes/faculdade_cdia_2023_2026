import os
import deepxde as dde
from utils.checkpoint import CheckpointManager

class PINN:
    def __init__(self, config, problem):
        self.config = config
        self.problem = problem
        self.data = problem["data"]
        self.net = problem["net"]
        self.model = dde.Model(self.data, self.net)
        self.history = None

    def train(self):
        # Obter configurações específicas do problema (se existirem)
        pinn_cfg = self.problem.get("pinn_config", {})
        
        # Pesos dinâmicos: PDE = 1.0, BCs = 100.0 (Harder enforcement)
        # DeepXDE organiza losses como [PDE, BC1, BC2, ..., IC]
        loss_weights = [1.0] # PDE
        if self.data.bcs:
            loss_weights += [100.0] * len(self.data.bcs) # BCs (inclui IC se passado em bcs)

        # Otimizador Adam
        self.model.compile("adam", lr=1e-3, loss_weights=loss_weights)
        
        # Configuração de Checkpoint via Manager
        max_keep = self.config.get("keep_checkpoints", 0)
        ckpt_manager = CheckpointManager(max_keep=max_keep)
        ckpt_dir = ckpt_manager.get_run_dir(self.config)
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
        save_period = self.config.get("checkpoint_every", 1000)
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
                self.model.restore(restore_path)
                self.model.train_state.step = latest_step
        
        # Treinamento Adam
        total_adam_iters = pinn_cfg.get("train_steps_adam", self.config.get("train_steps_adam", 15000))
        remaining_iters = total_adam_iters - latest_step
        
        if remaining_iters > 0:
            print(f">>> Iniciando treinamento ADAM por {remaining_iters} iterações (Total: {total_adam_iters})...")
            resampler = dde.callbacks.PDEPointResampler(period=1000)
            self.history = self.model.train(iterations=remaining_iters, callbacks=[resampler, checker, cleanup_cb, early_stopping], display_every=500)
        else:
            print(f">>> Treinamento ADAM já concluído (Step {latest_step} >= {total_adam_iters}). Pulando...")
            # Create a dummy history object if skipped, or just return None/empty
            # DeepXDE returns a LossHistory object. 
            # If we skip, we might not have history. 
            # For now, let's assume L-BFGS will run or we handle it.

        # Refinamento L-BFGS
        lbfgs_iters = pinn_cfg.get("train_steps_lbfgs", self.config.get("train_steps_lbfgs", 5000))
        if lbfgs_iters > 0:
            print(f">>> Refinando com L-BFGS por {lbfgs_iters} iterações...")
            self.model.compile("L-BFGS", loss_weights=loss_weights)
            self.history = self.model.train(iterations=lbfgs_iters, callbacks=[checker, cleanup_cb, early_stopping], display_every=500)
        
        # Save final model explicitly to run_dir (passed in config or inferred)
        # Note: self.config doesn't have run_dir directly, but ckpt_manager derived it.
        # Let's save to ckpt_dir/pinn_model.h5 which is what main.py expects (or main.py saves it itself?)
        # main.py tries to save it: pinn.model.save(os.path.join(run_dir, "pinn_model.h5"))
        # But main.py might not have access to the internal session if DeepXDE closes it?
        # No, DeepXDE keeps session open.
        
        # However, let's ensure it's saved here too just in case.
        save_path = os.path.join(ckpt_dir, "pinn_model.h5")
        self.model.save(save_path)
        print(f"Model saved to {save_path}")

        return self.history

    def predict(self, x):
        return self.model.predict(x)