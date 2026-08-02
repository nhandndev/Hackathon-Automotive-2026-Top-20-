"""Run the reference FastAPI DecisionEvent receiver for SE."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

AI_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AI_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Serve the reference SE DecisionEvent API"
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    try:
        import uvicorn
    except ImportError as exc:
        raise SystemExit(
            "uvicorn is missing; install AI/requirements.txt first"
        ) from exc
    uvicorn.run(
        "services.se_reference_api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        app_dir=str(AI_ROOT),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
