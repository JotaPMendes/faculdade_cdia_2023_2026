import requests
import time
import os
import sys

BASE_URL = "http://localhost:8000"

def test_e2e():
    # 1. Update Config
    print("Updating config...")
    try:
        config = requests.get(f"{BASE_URL}/config").json()
    except Exception as e:
        print(f"Failed to get config: {e}")
        sys.exit(1)
        
    config["train_steps_adam"] = 100
    config["train_steps_lbfgs"] = 0
    config["checkpoint_every"] = 50
    
    # Ensure boundary_conditions are valid (sometimes they might be missing or wrong type)
    if "boundary_conditions" not in config:
        config["boundary_conditions"] = {"Left": 1.0, "Right": 0.0}
        
    res = requests.post(f"{BASE_URL}/config", json=config)
    if res.status_code != 200:
        print(f"Failed to update config: {res.text}")
        sys.exit(1)
    print("Config updated.")

    # 2. Start Training
    print("Starting training...")
    res = requests.post(f"{BASE_URL}/train")
    if res.status_code != 200:
        print(f"Failed to start training: {res.text}")
        sys.exit(1)
        
    data = res.json()
    if data.get("status") == "error":
        print(f"Training failed to start: {data.get('message')}")
        # Try to stop existing
        requests.post(f"{BASE_URL}/stop")
        time.sleep(2)
        res = requests.post(f"{BASE_URL}/train")
        data = res.json()
        
    run_id = data["run_id"]
    print(f"Training started: {run_id}")

    # 3. Wait for completion
    print("Waiting for completion...")
    for _ in range(60): # Wait max 120s
        try:
            status = requests.get(f"{BASE_URL}/").json()["training_status"]
            print(f"Status: {status}")
            if status in ["COMPLETED", "ERROR", "STOPPED"]:
                break
        except:
            pass
        time.sleep(2)
    else:
        print("Timeout waiting for training to complete.")
        sys.exit(1)

    if status != "COMPLETED":
        print(f"Training finished with status: {status}")
        # Check logs if possible?
        sys.exit(1)
        
    print("Training completed successfully.")

    # 4. Verify files
    # We need to know where the results dir is relative to this script
    # Assuming this script is in tcc/
    results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", run_id)
    
    files_to_check = ["history.json", "metrics.json", "config.json"]
    for f in files_to_check:
        path = os.path.join(results_dir, f)
        if os.path.exists(path):
            print(f"✓ Found {f}")
        else:
            print(f"❌ Missing {f}")
            sys.exit(1)
            
    # Check for model file (DeepXDE produces checkpoints with varying names)
    model_files = [f for f in os.listdir(results_dir) if f.startswith("pinn_model.h5")]
    if model_files:
        print(f"✓ Found model files: {model_files[0]}...")
    else:
        print("❌ Missing pinn_model.h5*")
        sys.exit(1)
            
    print("All files verified.")

if __name__ == "__main__":
    test_e2e()
