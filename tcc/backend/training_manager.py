import asyncio
import os
import sys
from typing import Optional, List, Set
from datetime import datetime

class TrainingManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TrainingManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.process: Optional[asyncio.subprocess.Process] = None
        self.run_id: Optional[str] = None
        self.log_subscribers: Set[asyncio.Queue] = set()
        self.status = "IDLE" # IDLE, RUNNING, COMPLETED, ERROR, STOPPED

    async def start_training(self, run_dir: str):
        if self.process and self.process.returncode is None:
            raise Exception("Training is already running")

        self.status = "RUNNING"
        self.run_id = os.path.basename(run_dir)
        
        # Caminho absoluto para o main.py na raiz
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        main_script = os.path.join(root_dir, "main.py")

        # Comando para rodar
        cmd = [sys.executable, "-u", main_script, "--run-dir", run_dir]

        try:
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=root_dir,
                limit=1024*1024 # 1MB buffer limit
            )
            
            # Iniciar tarefa de leitura de logs em background
            asyncio.create_task(self._read_logs())
            
            return self.process.pid
        except Exception as e:
            self.status = "ERROR"
            await self._broadcast_log(f"Failed to start process: {str(e)}")
            raise e

    async def stop_training(self):
        if self.process and self.process.returncode is None:
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self.process.kill()
            self.status = "STOPPED"
            await self._broadcast_log("--- Training Stopped by User ---")

    async def _read_logs(self):
        if not self.process or not self.process.stdout:
            return

        try:
            while True:
                line = await self.process.stdout.readline()
                if not line:
                    break
                
                decoded_line = line.decode('utf-8').rstrip()
                print(f"[TRAIN] {decoded_line}")
                await self._broadcast_log(decoded_line)

            # Processo terminou
            return_code = await self.process.wait()
            if return_code == 0:
                self.status = "COMPLETED"
                await self._broadcast_log("--- Training Completed Successfully ---")
            elif self.status != "STOPPED": # Se não foi parado manualmente
                self.status = "ERROR"
                await self._broadcast_log(f"--- Process finished with exit code {return_code} ---")

        except Exception as e:
            print(f"Error reading logs: {e}")
            await self._broadcast_log(f"Internal Error reading logs: {e}")

    async def _broadcast_log(self, message: str):
        # Enviar para todos os subscribers
        for q in list(self.log_subscribers):
            try:
                q.put_nowait(message)
            except asyncio.QueueFull:
                pass # Drop log if client is too slow

    async def subscribe(self) -> asyncio.Queue:
        q = asyncio.Queue()
        self.log_subscribers.add(q)
        # Enviar status atual imediatamente
        await q.put(f"--- Connected to Log Stream (Status: {self.status}) ---")
        return q

    def unsubscribe(self, q: asyncio.Queue):
        if q in self.log_subscribers:
            self.log_subscribers.remove(q)

training_manager = TrainingManager()
