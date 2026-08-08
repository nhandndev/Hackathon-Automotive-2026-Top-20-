import logging
import warnings
from pathlib import Path
import joblib
import sklearn

from .face_landmarker import LANDMARK_BACKEND
from .ml_features import feature_names, fatigue_feature_names, distraction_feature_names, architect_v2_feature_names
from .label_contract import FINAL_LABELS

logger = logging.getLogger("model_contract")

def load_driver_artifact(path: Path) -> dict:
    path = Path(path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Challenge-2 model not found: {path}")
    if path.suffix.lower() != ".joblib":
        raise ValueError(f"Challenge-2 model must be .joblib: {path}")
    
    artifact = joblib.load(path)
    if not isinstance(artifact, dict):
        raise ValueError("Challenge-2 joblib artifact must contain a dict bundle")
    return artifact

def validate_driver_artifact(artifact: dict) -> None:
    architecture = artifact.get("architecture", "legacy_5class")
    if architecture not in ("legacy_5class", "hierarchical_v1", "hierarchical_v2", "architect_v2"):
        raise ValueError(f"Unsupported architecture: {architecture}")
    
    # Check scikit-learn version if present
    sk_ver = artifact.get("scikit_learn_version")
    if sk_ver:
        current_ver = sklearn.__version__
        # check major/minor mismatch
        if sk_ver.split(".")[:2] != current_ver.split(".")[:2]:
            warnings.warn(
                f"scikit-learn version mismatch: model trained with {sk_ver}, "
                f"runtime is {current_ver}. This may cause serialization errors.",
                RuntimeWarning
            )

    # Check landmark backend
    artifact_backend = artifact.get("landmark_backend")
    if artifact_backend is not None:
        if artifact_backend != LANDMARK_BACKEND:
            raise ValueError(
                f"Challenge-2 landmark backend mismatch: artifact={artifact_backend!r}, runtime={LANDMARK_BACKEND!r}."
            )
    else:
        if architecture == "hierarchical_v1":
            warnings.warn(
                f"Hierarchical model missing landmark_backend metadata. Assuming {LANDMARK_BACKEND!r}.",
                RuntimeWarning
            )
        else:
            raise ValueError("Challenge-2 model is missing 'landmark_backend' metadata and cannot be verified.")

    # Validate classes
    model_classes = artifact.get("model_classes")
    if not model_classes:
        raise ValueError("Model bundle is missing 'model_classes'")
    for cls in model_classes:
        if cls not in FINAL_LABELS:
            raise ValueError(f"Unsupported class in model_classes: {cls}")

    # Validate based on architecture
    if architecture == "legacy_5class":
        model = artifact.get("model")
        if model is None:
            raise ValueError("legacy_5class model is missing 'model' key")
        f_names = artifact.get("feature_names")
        if f_names != feature_names():
            raise ValueError("legacy_5class feature schema mismatch")
        if getattr(model, "n_features_in_", None) != len(feature_names()):
            raise ValueError(f"legacy_5class features count mismatch: model has {getattr(model, 'n_features_in_', None)}, expected {len(feature_names())}")
            
    elif architecture == "hierarchical_v1":
        f_model = artifact.get("fatigue_model")
        d_model = artifact.get("distraction_model")
        if f_model is None or d_model is None:
            raise ValueError("hierarchical_v1 model is missing fatigue_model or distraction_model")
            
        fatigue_names_cached = artifact.get("fatigue_feature_names")
        distraction_names_cached = artifact.get("distraction_feature_names")
        
        if fatigue_names_cached != fatigue_feature_names():
            raise ValueError("Fatigue feature schema mismatch for hierarchical_v1")
        if distraction_names_cached != distraction_feature_names():
            raise ValueError("Distraction feature schema mismatch for hierarchical_v1")
            
        if getattr(f_model, "n_features_in_", None) != 52:
            raise ValueError(f"hierarchical_v1 fatigue features mismatch: model has {getattr(f_model, 'n_features_in_', None)}, expected 52")
        if getattr(d_model, "n_features_in_", None) != 30:
            raise ValueError(f"hierarchical_v1 distraction features mismatch: model has {getattr(d_model, 'n_features_in_', None)}, expected 30")
            
        thresh = artifact.get("fusion", {}).get("distracted_threshold")
        if thresh is None or not (0.0 <= thresh <= 1.0):
            raise ValueError(f"Invalid distracted_threshold: {thresh}")
            
    elif architecture == "hierarchical_v2":
        f_model = artifact.get("fatigue_model")
        d_model = artifact.get("distraction_model")
        if f_model is None or d_model is None:
            raise ValueError("hierarchical_v2 model is missing fatigue_model or distraction_model")
            
        fatigue_names_cached = artifact.get("fatigue_feature_names")
        distraction_names_cached = artifact.get("distraction_feature_names")
        
        if fatigue_names_cached != feature_names():
            raise ValueError("Fatigue feature schema mismatch for hierarchical_v2")
        if distraction_names_cached != distraction_feature_names():
            raise ValueError("Distraction feature schema mismatch for hierarchical_v2")
            
        if getattr(f_model, "n_features_in_", None) != 59:
            raise ValueError(f"hierarchical_v2 fatigue features mismatch: model has {getattr(f_model, 'n_features_in_', None)}, expected 59")
        if getattr(d_model, "n_features_in_", None) != 30:
            raise ValueError(f"hierarchical_v2 distraction features mismatch: model has {getattr(d_model, 'n_features_in_', None)}, expected 30")
            
        thresh = artifact.get("fusion", {}).get("distracted_threshold")
        if thresh is None or not (0.0 <= thresh <= 1.0):
            raise ValueError(f"Invalid distracted_threshold: {thresh}")
            
    elif architecture == "architect_v2":
        model = artifact.get("model")
        if model is None:
            raise ValueError("architect_v2 model is missing 'model' key")
        names = artifact.get("feature_names")
        if names != architect_v2_feature_names():
            raise ValueError("architect_v2 feature schema mismatch")
        if getattr(model, "n_features_in_", None) != 84:
            raise ValueError(f"architect_v2 features count mismatch: model has {getattr(model, 'n_features_in_', None)}, expected 84")
        if artifact.get("feature_schema") != "unified_84_legacy59_hand25":
            raise ValueError("architect_v2 feature_schema metadata mismatch")

def validate_feature_contract(fatigue_names: list, distraction_names: list) -> None:
    # This validates feature schemas against expected lists in code
    expected_f59 = feature_names()
    expected_f52 = fatigue_feature_names()
    expected_d30 = distraction_feature_names()
    
    if fatigue_names == expected_f59:
        pass
    elif fatigue_names == expected_f52:
        pass
    else:
        raise ValueError("Fatigue features do not match either 52-feature or 59-feature schema")
        
    if distraction_names != expected_d30:
        raise ValueError("Distraction features do not match expected 30-feature schema")

def describe_driver_artifact(artifact: dict) -> dict:
    architecture = artifact.get("architecture", "legacy_5class")
    if architecture == "architect_v2":
        return {
            "architecture": "architect_v2",
            "feature_schema": artifact.get("feature_schema", "unified_84_legacy59_hand25"),
            "n_features": len(artifact.get("feature_names", [])),
            "classes": artifact.get("model_classes", []),
            "landmark_backend": artifact.get("landmark_backend"),
            "hand_backend": artifact.get("hand_backend", "mock-hand-detector"),
            "scikit_learn_version": artifact.get("scikit_learn_version"),
        }
    return {
        "architecture": architecture,
        "fatigue_feature_schema": artifact.get("fatigue_feature_schema", "legacy_59" if architecture == "legacy_5class" else "fatigue_v1_3_5_7_10"),
        "fatigue_n_features": len(artifact.get("fatigue_feature_names", artifact.get("feature_names", []))),
        "distraction_feature_schema": artifact.get("distraction_feature_schema", "distraction_v1_1_3" if "distraction_model" in artifact else None),
        "distraction_n_features": len(artifact.get("distraction_feature_names", [])),
        "threshold": artifact.get("fusion", {}).get("distracted_threshold"),
        "landmark_backend": artifact.get("landmark_backend"),
        "scikit_learn_version": artifact.get("scikit_learn_version"),
    }
