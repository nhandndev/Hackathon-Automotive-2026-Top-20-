import sys
import argparse
from pathlib import Path

AI_ROOT = Path(__file__).resolve().parents[1]
if str(AI_ROOT) not in sys.path:
    sys.path.insert(0, str(AI_ROOT))

from core.challenge2_driver.model_contract import (
    load_driver_artifact,
    validate_driver_artifact,
    describe_driver_artifact
)

def main():
    parser = argparse.ArgumentParser(description="Inspect a Challenge-2 driver model.")
    parser.add_argument("model_path", type=Path, help="Path to joblib model file")
    args = parser.parse_args()
    
    try:
        artifact = load_driver_artifact(args.model_path)
        validate_driver_artifact(artifact)
        desc = describe_driver_artifact(artifact)
        
        if desc['architecture'] == 'architect_v2':
            print(f"architecture: {desc['architecture']}")
            print(f"feature schema: {desc['feature_schema']}")
            print(f"n_features: {desc['n_features']}")
            print(f"classes: {','.join(desc['classes'])}")
            print(f"landmark backend: {desc['landmark_backend']}")
            print(f"hand backend: {desc['hand_backend']}")
            print(f"sklearn: {desc['scikit_learn_version']}")
        else:
            print(f"architecture: {desc['architecture']}")
            print(f"fatigue schema: {desc['fatigue_feature_schema']}")
            print(f"fatigue n_features: {desc['fatigue_n_features']}")
            print(f"distraction schema: {desc['distraction_feature_schema']}")
            print(f"distraction n_features: {desc['distraction_n_features']}")
            print(f"threshold: {desc['threshold']}")
            print(f"landmark backend: {desc['landmark_backend']}")
            print(f"sklearn: {desc['scikit_learn_version']}")
        print("contract: PASS")
        sys.exit(0)
    except Exception as e:
        print(f"contract: FAIL ({e})")
        sys.exit(1)

if __name__ == "__main__":
    main()
