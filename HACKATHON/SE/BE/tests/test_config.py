import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_environment_overrides_and_comma_separated_cors(monkeypatch, tmp_path):
    monkeypatch.setenv("DATASET_DIR", str(tmp_path))
    monkeypatch.setenv("STREAM_FPS", "10")
    monkeypatch.setenv("CORS_ORIGINS", "http://a.example,http://b.example")

    configured = Settings(_env_file=None)

    assert configured.DATASET_DIR == tmp_path
    assert configured.STREAM_FPS == 10
    assert configured.FRAME_INTERVAL_SEC == 0.1
    assert configured.CORS_ORIGINS == ["http://a.example", "http://b.example"]


def test_wildcard_cors_is_rejected():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, CORS_ORIGINS="*")
