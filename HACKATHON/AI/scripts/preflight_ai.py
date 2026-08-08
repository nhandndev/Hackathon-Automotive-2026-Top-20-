import sys
from pathlib import Path
import logging

AI_ROOT = Path(__file__).resolve().parents[1]
if str(AI_ROOT) not in sys.path:
    sys.path.insert(0, str(AI_ROOT))

def main():
    print("AI PREFLIGHT CHECK STARTING...")
    
    # 1. Python version
    py_ver = sys.version_info
    if py_ver.major != 3:
        print("[FAIL] Python major version must be 3")
        sys.exit(1)
    print(f"[OK] Python {py_ver.major}.{py_ver.minor}.{py_ver.micro}")
    
    # 2. Required packages
    packages = [
        ("numpy", "NumPy"),
        ("sklearn", "scikit-learn"),
        ("onnxruntime", "ONNX Runtime"),
        ("cv2", "OpenCV"),
        ("torch", "Torch"),
        ("ultralytics", "Ultralytics"),
        ("yaml", "PyYAML"),
        ("joblib", "Joblib")
    ]
    for pkg_name, name in packages:
        try:
            __import__(pkg_name)
            print(f"[OK] {name}")
        except ImportError:
            print(f"[FAIL] {name} is missing")
            sys.exit(1)
            
    # 3. ONNX Runtime providers and CUDA check
    import torch
    cuda_available = torch.cuda.is_available()
    print(f"\nTorch CUDA: {'YES' if cuda_available else 'NO'}")
    if cuda_available:
        print(f"GPU: {torch.cuda.get_device_name(0)}")
    else:
        print("[FAIL] CUDA is required for AI model inference")
        sys.exit(1)

    import onnxruntime as ort
    providers = ort.get_available_providers()
    print("\nONNX providers:")
    for p in providers:
        print(f"  {p}")
    if "CUDAExecutionProvider" not in providers:
        print("[FAIL] CUDAExecutionProvider is missing from ONNX Runtime")
        sys.exit(1)
        
    # 4. Check model files existence
    models_dir = AI_ROOT / "models"
    model_files = [
        "face_detection_yunet_2023mar.onnx",
        "face_landmark_468.onnx",
        "yolov8s_finetuned_carla_v2.pt"
    ]
    for mf in model_files:
        path = models_dir / mf
        if path.is_file():
            print(f"[OK] {mf}")
        else:
            print(f"[FAIL] Missing model file: {path}")
            sys.exit(1)
            
    # 5. Resolve and validate the single production Driver-State artifact.
    from core.runtime.model_registry import resolve_driver_model
    from core.challenge2_driver.model_contract import (
        describe_driver_artifact,
        load_driver_artifact,
        validate_driver_artifact,
    )
    try:
        current_model = resolve_driver_model(AI_ROOT, None)
        artifact = load_driver_artifact(current_model)
        validate_driver_artifact(artifact)
        description = describe_driver_artifact(artifact)
        if description.get("hand_backend") == "mock-hand-detector":
            print(
                "[WARN] Production model uses the compatibility "
                "mock-hand feature backend"
            )
        print(
            f"[OK] {current_model.name} resolved via registry "
            f"({description['architecture']})"
        )
    except Exception as e:
        print(f"[FAIL] Production model registry: {e}")
        sys.exit(1)
        
    print("\nAI PREFLIGHT PASSED")
    sys.exit(0)

if __name__ == "__main__":
    main()
