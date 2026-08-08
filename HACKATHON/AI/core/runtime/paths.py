from pathlib import Path

def ensure_output_dir(path: Path) -> Path:
    p = Path(path).resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p

def ensure_output_file(path: Path) -> Path:
    p = Path(path).resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    return p

def resolve_json_output(output: Path | None, predictions: Path) -> Path:
    predictions = Path(predictions).resolve()
    if output is None:
        if predictions.is_dir():
            return ensure_output_file(predictions / "evaluation.json")
        return ensure_output_file(predictions.parent / f"{predictions.stem}.evaluation.json")

    path = Path(output).resolve()
    if path.exists() and path.is_dir():
        return ensure_output_file(path / "evaluation.json")

    # If it has no suffix, treat it as a directory to create
    if not path.exists() and path.suffix == "":
        path.mkdir(parents=True, exist_ok=True)
        return ensure_output_file(path / "evaluation.json")

    return ensure_output_file(path)

def resolve_csv_output(output_csv: Path | None, out_dir: Path | None, trip_name: str) -> Path:
    if output_csv is not None:
        return ensure_output_file(output_csv)
    
    od = Path(out_dir) if out_dir is not None else Path("AI/artifacts/predictions")
    return ensure_output_file(od / f"{trip_name}.csv")
