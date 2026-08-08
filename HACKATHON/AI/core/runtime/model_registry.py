from pathlib import Path
import yaml

def resolve_driver_model(
    ai_root: Path,
    explicit_path: Path | None,
) -> Path:
    ai_root = Path(ai_root).resolve()
    if explicit_path is not None:
        model = Path(explicit_path)
    else:
        registry_path = (
            ai_root
            / "configs"
            / "model_registry.yaml"
        )
        if not registry_path.is_file():
            raise FileNotFoundError(f"Model registry file not found: {registry_path}")
            
        registry = yaml.safe_load(
            registry_path.read_text(
                encoding="utf-8"
            )
        )
        rel = registry["challenge2"]["production"]["artifact"]
        model = ai_root / rel

    model = model.resolve()

    if model.suffix.lower() != ".joblib":
        raise ValueError(
            "Challenge-2 model must "
            f"be .joblib: {model}"
        )

    if not model.is_file():
        raise FileNotFoundError(
            "Challenge-2 model not found: "
            f"{model}"
        )

    return model
