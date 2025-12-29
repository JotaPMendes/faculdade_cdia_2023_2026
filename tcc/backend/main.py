import sys
import os
import asyncio
from fastapi import FastAPI, WebSocket, BackgroundTasks, HTTPException, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
import shutil
import subprocess

# Adicionar raiz ao path para importar módulos do projeto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import CONFIG
from backend.training_manager import training_manager

app = FastAPI(title="PINN Benchmark API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Results Directory for Static Access
results_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")
os.makedirs(results_dir, exist_ok=True)
app.mount("/results", StaticFiles(directory=results_dir), name="results")

# --- SCHEMAS ---
class ConfigUpdate(BaseModel):
    problem: str
    mesh_file: str
    N_data: int
    N_test: int
    use_mesh: bool
    boundary_conditions: Dict[str, float]
    pinn_config: Optional[Dict[str, Any]] = None
    # Optional fields for specific problems
    Lx: Optional[float] = None
    Ly: Optional[float] = None
    T_train: Optional[float] = None
    alpha: Optional[float] = None
    c: Optional[float] = None
    frequency: Optional[float] = None
    sigma: Optional[float] = None
    mu: Optional[float] = None
    Nx_train: Optional[int] = None
    Ny_train: Optional[int] = None

class MeshGenRequest(BaseModel):
    type: str

# --- ROUTES ---

@app.get("/")
def read_root():
    return {"status": "online", "service": "PINN Benchmark Backend", "training_status": training_manager.status}

@app.get("/config")
def get_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return json.load(f)
    return {}

@app.get("/metrics")
def get_metrics():
    metrics_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results", "latest", "metrics.json")
    if os.path.exists(metrics_path):
        try:
            with open(metrics_path, "r") as f:
                return json.load(f)
        except Exception as e:
            return {"error": str(e)}
    return {}

@app.get("/meshes")
def list_meshes():
    mesh_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "meshes", "files")
    if not os.path.exists(mesh_dir):
        return []
    return [f for f in os.listdir(mesh_dir) if f.endswith(".msh")]

@app.get("/runs")
def list_runs():
    results_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")
    if not os.path.exists(results_dir):
        return []
    
    runs = []
    for d in os.listdir(results_dir):
        if d == "latest": continue
        run_path = os.path.join(results_dir, d)
        if os.path.isdir(run_path):
            metrics = {}
            timestamp = os.path.getctime(run_path)
            try:
                with open(os.path.join(run_path, "metrics.json"), "r") as f:
                    metrics = json.load(f)
            except:
                pass
            
            runs.append({
                "id": d,
                "timestamp": datetime.fromtimestamp(timestamp).isoformat(),
                "metrics": metrics
            })
    
    runs.sort(key=lambda x: x["timestamp"], reverse=True)
    return runs

@app.get("/runs/{run_id}")
def get_run_details(run_id: str):
    results_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")
    run_path = os.path.join(results_dir, run_id)
    
    if not os.path.exists(run_path):
        raise HTTPException(status_code=404, detail="Run not found")
        
    details = {"id": run_id}
    
    for filename in ["metrics.json", "config.json", "model_summary.json"]:
        try:
            with open(os.path.join(run_path, filename), "r") as f:
                key = filename.split(".")[0]
                details[key] = json.load(f)
        except:
            pass
            
    return details

@app.delete("/runs/{run_id}")
def delete_run(run_id: str):
    results_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")
    run_path = os.path.join(results_dir, run_id)
    
    if not os.path.exists(run_path):
        raise HTTPException(status_code=404, detail="Run not found")
        
    try:
        shutil.rmtree(run_path)
        return {"status": "success", "message": f"Run {run_id} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/config")
def update_config(new_config: ConfigUpdate):
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
    
    current_config = {}
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            current_config = json.load(f)
            
    current_config.update(new_config.dict(exclude_unset=True))
    
    if "slice_config" not in current_config:
        current_config["slice_config"] = {
            "type": "radial",
            "p_start": [0.5, 0.0],
            "p_end": [1.0, 0.0],
            "xlabel": "Raio (r)"
        }
    if "scaling_factor" not in current_config:
        current_config["scaling_factor"] = 100.0
    if "alpha" not in current_config:
        current_config["alpha"] = 0.01
    if "c" not in current_config:
        current_config["c"] = 1.0
    if "Nx_train" not in current_config:
        current_config["Nx_train"] = 50
    if "Ny_train" not in current_config:
        current_config["Ny_train"] = 50

    # Ensure train_box is set for Poisson 2D
    if current_config.get("problem") == "poisson_2d":
        Lx = current_config.get("Lx", 1.0)
        Ly = current_config.get("Ly", 1.0)
        current_config["train_box"] = [0.0, 0.0, float(Lx), float(Ly)]

    try:
        with open(config_path, "w") as f:
            json.dump(current_config, f, indent=4)
        return {"status": "success", "message": "Config updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mesh/upload")
async def upload_mesh(file: UploadFile = File(...)):
    if not file.filename.endswith('.msh'):
        raise HTTPException(status_code=400, detail="Only .msh files are allowed")
        
    mesh_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "meshes", "files")
    os.makedirs(mesh_dir, exist_ok=True)
    
    file_path = os.path.join(mesh_dir, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"status": "success", "message": f"Mesh {file.filename} uploaded", "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")

@app.get("/docs/{filename}")
def get_documentation(filename: str):
    allowed_files = {
        "readme": "README.md",
        "architecture": "docs/ARCHITECTURE.md",
        "learnings": "docs/LEARNINGS.md",
        "old_docs": "docs/OLD_TECHNICAL_DOCS.md"
    }
    
    if filename not in allowed_files:
        raise HTTPException(status_code=404, detail="Doc not found")
        
    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), allowed_files[filename])
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
        
    with open(file_path, "r") as f:
        return {"content": f.read()}

@app.post("/train")
async def start_training():
    if training_manager.status == "RUNNING":
        return {"status": "error", "message": "Training already in progress"}
    
    run_id = datetime.now().strftime("run_%Y%m%d_%H%M%S")
    results_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")
    run_dir = os.path.join(results_dir, run_id)
    os.makedirs(run_dir, exist_ok=True)
    
    try:
        pid = await training_manager.start_training(run_dir)
        return {"status": "started", "pid": pid, "run_id": run_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stop")
async def stop_training():
    await training_manager.stop_training()
    return {"status": "stopped"}

@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    queue = await training_manager.subscribe()
    
    try:
        while True:
            # Esperar por logs
            log_line = await queue.get()
            await websocket.send_text(log_line)
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WS Error: {e}")
    finally:
        training_manager.unsubscribe(queue)
        # Não chamamos websocket.close() aqui se já foi desconectado
        # O WebSocketDisconnect já lida com o fechamento

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
