import subprocess
import time
import os
import signal
import sys
import webbrowser

def run_app():
    print("🚀 Starting PINN Benchmark Full Stack...")
    
    # 1. Start Backend
    print("🐍 Starting Backend (FastAPI)...")
    backend_env = os.environ.copy()
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--port", "8000"],
        cwd="backend",
        env=backend_env
    )
    
    # 2. Start Frontend
    print("⚛️ Starting Frontend (Vite)...")
    frontend_process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd="frontend",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    print("✅ Services Started!")
    print("   Backend: http://localhost:8000")
    print("   Frontend: http://localhost:5173")
    
    # Open Browser
    time.sleep(2)
    webbrowser.open("http://localhost:5173")
    
    try:
        while True:
            time.sleep(1)
            if backend_process.poll() is not None:
                print("❌ Backend crashed!")
                break
            if frontend_process.poll() is not None:
                print("❌ Frontend crashed!")
                # Print frontend error
                print(frontend_process.stderr.read())
                break
    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
        backend_process.terminate()
        frontend_process.terminate()
        print("👋 Goodbye!")

if __name__ == "__main__":
    run_app()
