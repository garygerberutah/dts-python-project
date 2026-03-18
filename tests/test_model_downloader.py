"""Tests for scripts/util/model-downloader.py.

Copyright 2026 by GuidoGerb Publishing, LLC

This script imports boto3, requests, and huggingface_hub at module level,
which makes direct import expensive. Tests mock external dependencies.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parent.parent
MODELS_JSON = ROOT / "scripts" / "all-guidogerb-models.json"


@pytest.fixture()
def _mock_external_deps():
    """Mock boto3, requests, and huggingface_hub before importing the module."""
    mock_boto3 = MagicMock()
    mock_requests = MagicMock()
    mock_hf = MagicMock()

    with patch.dict(
        "sys.modules",
        {
            "boto3": mock_boto3,
            "boto3.s3.transfer": MagicMock(),
            "requests": mock_requests,
            "huggingface_hub": mock_hf,
        },
    ):
        yield mock_boto3, mock_requests, mock_hf


# --- JSON manifest tests (no mocks needed) ---


def test_models_json_exists():
    """all-guidogerb-models.json exists at the expected path."""
    assert MODELS_JSON.exists(), f"Missing {MODELS_JSON}"


def test_models_json_is_valid():
    """all-guidogerb-models.json is valid JSON with required structure."""
    data = json.loads(MODELS_JSON.read_text())
    assert "s3_bucket" in data
    assert "models" in data
    assert isinstance(data["models"], list)
    assert len(data["models"]) > 0


def test_models_json_s3_bucket():
    """S3 bucket is the expected value."""
    data = json.loads(MODELS_JSON.read_text())
    assert data["s3_bucket"] == "ggp-models"


def test_models_json_required_fields():
    """Every model entry has all required fields."""
    data = json.loads(MODELS_JSON.read_text())
    required = {"repo_id", "s3_prefix", "category", "architecture", "display_name", "description"}
    for model in data["models"]:
        missing = required - set(model.keys())
        assert not missing, f"{model.get('repo_id', '?')} missing fields: {missing}"


def test_models_json_unique_repo_ids():
    """No duplicate repo_id entries."""
    data = json.loads(MODELS_JSON.read_text())
    repo_ids = [m["repo_id"] for m in data["models"]]
    assert len(repo_ids) == len(set(repo_ids)), "Duplicate repo_ids found"


def test_models_json_repo_id_format():
    """Every repo_id follows the org/model format."""
    data = json.loads(MODELS_JSON.read_text())
    for model in data["models"]:
        assert "/" in model["repo_id"], f"Invalid repo_id: {model['repo_id']}"
        parts = model["repo_id"].split("/")
        assert len(parts) == 2, f"repo_id should be org/model: {model['repo_id']}"


def test_models_json_no_empty_strings():
    """No model has empty string values for required fields."""
    data = json.loads(MODELS_JSON.read_text())
    for model in data["models"]:
        for key in ("repo_id", "s3_prefix", "category", "architecture"):
            assert model[key].strip(), f"{model['repo_id']} has empty {key}"


# --- Script module tests (with mocks) ---


def test_load_models_function(_mock_external_deps):
    """load_models returns (bucket, models) from JSON."""
    import importlib

    mod = importlib.import_module("scripts.util.model-downloader")
    bucket, models = mod.load_models(str(MODELS_JSON))
    assert bucket == "ggp-models"
    assert isinstance(models, list)
    assert len(models) > 0


def test_transfer_config_exists(_mock_external_deps):
    """transfer_config is created with memory-safe settings."""
    import importlib

    mod = importlib.import_module("scripts.util.model-downloader")
    assert hasattr(mod, "transfer_config")


def test_stream_model_to_s3_function_exists(_mock_external_deps):
    """stream_model_to_s3 function is defined."""
    import importlib

    mod = importlib.import_module("scripts.util.model-downloader")
    assert callable(mod.stream_model_to_s3)


def test_verify_model_in_s3_function_exists(_mock_external_deps):
    """verify_model_in_s3 function is defined."""
    import importlib

    mod = importlib.import_module("scripts.util.model-downloader")
    assert callable(mod.verify_model_in_s3)


def test_verify_all_function_exists(_mock_external_deps):
    """verify_all function is defined."""
    import importlib

    mod = importlib.import_module("scripts.util.model-downloader")
    assert callable(mod.verify_all)


def test_main_function_exists(_mock_external_deps):
    """main function is defined."""
    import importlib

    mod = importlib.import_module("scripts.util.model-downloader")
    assert callable(mod.main)


def test_valid_extensions_in_stream_logic(_mock_external_deps):
    """The download logic filters for .safetensors, .json, etc."""
    import importlib
    import inspect

    mod = importlib.import_module("scripts.util.model-downloader")
    source = inspect.getsource(mod.stream_model_to_s3)
    assert ".safetensors" in source
    assert ".json" in source


def test_hf_token_read_from_env(_mock_external_deps):
    """HF_TOKEN is read from the HF_TOKEN environment variable."""
    import importlib
    import os

    with patch.dict(os.environ, {"HF_TOKEN": "test-token-123"}):
        mod = importlib.import_module("scripts.util.model-downloader")
        importlib.reload(mod)
        assert mod.HF_TOKEN == "test-token-123"


def test_default_models_json_path(_mock_external_deps):
    """DEFAULT_MODELS_JSON points to the expected file."""
    import importlib

    mod = importlib.import_module("scripts.util.model-downloader")
    assert mod.DEFAULT_MODELS_JSON.name == "all-guidogerb-models.json"
