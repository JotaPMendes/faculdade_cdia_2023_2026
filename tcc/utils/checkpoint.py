import os
import json
import hashlib
import shutil
from datetime import datetime

class CheckpointManager:
    def __init__(self, base_dir="checkpoints", max_keep=3):
        self.base_dir = base_dir
        self.max_keep = max_keep
        self.registry_path = os.path.join(base_dir, "registry.json")
        self._ensure_base_dir()
        self.registry = self._load_registry()

    def _ensure_base_dir(self):
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

    def _load_registry(self):
        if os.path.exists(self.registry_path):
            try:
                with open(self.registry_path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    def _save_registry(self):
        with open(self.registry_path, 'w') as f:
            json.dump(self.registry, f, indent=2)

    def _hash_config(self, config):
        """Gera um hash único para a configuração (ignorando chaves não essenciais se necessário)."""
        # Ordena chaves para garantir determinismo
        config_str = json.dumps(config, sort_keys=True)
        return hashlib.md5(config_str.encode('utf-8')).hexdigest()

    def get_run_dir(self, config):
        """
        Retorna o diretório de checkpoint para a configuração dada.
        Se a configuração for nova, cria uma nova entrada no registro.
        """
        problem_name = config.get("problem", "unknown")
        config_hash = self._hash_config(config)
        
        # Estrutura do registro: { problem_name: { config_hash: { run_id: "run_001", config: {...}, last_used: "..." } } }
        if problem_name not in self.registry:
            self.registry[problem_name] = {}
            
        problem_registry = self.registry[problem_name]
        
        if config_hash in problem_registry:
            # Configuração existente
            entry = problem_registry[config_hash]
            entry["last_used"] = datetime.now().isoformat()
            run_id = entry["run_id"]
            print(f">>> Configuração encontrada no registro: {run_id}")
        else:
            # Nova configuração
            # Determinar próximo run_id
            existing_ids = [e["run_id"] for e in problem_registry.values()]
            if not existing_ids:
                next_id = 1
            else:
                # Extrai números de "run_XXX"
                ids_nums = [int(rid.split("_")[1]) for rid in existing_ids]
                next_id = max(ids_nums) + 1
            
            run_id = f"run_{next_id:03d}"
            problem_registry[config_hash] = {
                "run_id": run_id,
                "config": config,
                "created_at": datetime.now().isoformat(),
                "last_used": datetime.now().isoformat()
            }
            print(f">>> Nova configuração detectada. Criando: {run_id}")
            
        self._save_registry()
        
        # Caminho final: checkpoints/problem_name/run_id
        run_dir = os.path.join(self.base_dir, problem_name, run_id)
        if not os.path.exists(run_dir):
            os.makedirs(run_dir)
            
        return run_dir

    def cleanup(self, run_dir):
        """
        Mantém apenas os N checkpoints mais recentes no diretório.
        DeepXDE gera arquivos: model.ckpt-STEP.ckpt.data..., .index, .meta
        """
        if not os.path.exists(run_dir):
            return

        # Agrupar arquivos por step
        files = os.listdir(run_dir)
        checkpoints = {} # step -> [files]
        
        for f in files:
            if f.startswith("model.ckpt-") and ".ckpt." in f:
                # Ex: model.ckpt-1000.ckpt.index
                try:
                    step = int(f.split("-")[1].split(".")[0])
                    if step not in checkpoints:
                        checkpoints[step] = []
                    checkpoints[step].append(f)
                except:
                    continue
        
        # Se tivermos mais que max_keep, deletar os mais antigos
        steps = sorted(checkpoints.keys())
        if len(steps) > self.max_keep:
            to_delete = steps[:-self.max_keep] # Todos exceto os últimos N
            print(f">>> Limpeza de Checkpoints: Removendo steps antigos {to_delete}...")
            
            for step in to_delete:
                for filename in checkpoints[step]:
                    file_path = os.path.join(run_dir, filename)
                    try:
                        os.remove(file_path)
                    except OSError as e:
                        print(f"Erro ao deletar {file_path}: {e}")
