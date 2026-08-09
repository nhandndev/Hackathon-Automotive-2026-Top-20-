import os
import hashlib
import json
import zipfile
from datetime import datetime

def hash_file(filepath):
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        buf = f.read(65536)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(65536)
    return hasher.hexdigest()

def bundle_evaluator():
    print("Bundle Evaluator Started...")
    
    # In a real environment, we would access the actual models and data
    # Because we are running as an Agent without the large model weights/data
    # we cannot fully execute this on real data.
    print("WARNING: Script created but not tested with real model/data. Need Hung/Tam to provide and run.")
    
    target_dir = os.path.join(os.path.dirname(__file__), "..", "01_reproducibility")
    os.makedirs(target_dir, exist_ok=True)
    
    bundle_name = os.path.join(target_dir, "evaluation_bundle.zip")
    manifest_name = os.path.join(target_dir, "manifest.json")
    
    files_to_bundle = [
        # Example paths to be provided by owner
        # "HACKATHON/AI/models/best.pt",
        # "HACKATHON/AI/configs/eval_cfg.yaml"
    ]
    
    manifest = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "files": {}
    }
    
    # Dummy logic to create a zip if files existed
    with zipfile.ZipFile(bundle_name, 'w') as zf:
        for f in files_to_bundle:
            if os.path.exists(f):
                zf.write(f, os.path.basename(f))
                manifest["files"][os.path.basename(f)] = hash_file(f)
            else:
                print(f"File missing: {f}")
                
    with open(manifest_name, 'w', encoding='utf-8') as mf:
        json.dump(manifest, mf, indent=2)
        
    print(f"Bundle created at: {bundle_name}")
    print(f"Manifest created at: {manifest_name}")

if __name__ == "__main__":
    bundle_evaluator()
