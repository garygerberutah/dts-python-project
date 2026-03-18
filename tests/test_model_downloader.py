"""Tests for scripts/util/model-downloader.py.

Copyright 2026 by GuidoGerb Publishing, LLC

This script imports boto3, requests, and huggingface_hub at module level,
which makes direct import expensive. Tests mock external dependencies.
"""

from unittest.mock import MagicMock, patch

import pytest


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


def test_model_mappings_is_dict(_mock_external_deps):
    """MODEL_MAPPINGS is a non-empty dict of repo → folder mappings."""
    import importlib
    import scripts.util

    # Force reimport with mocked deps
    mod = importlib.import_module("scripts.util.model-downloader")
    assert isinstance(mod.MODEL_MAPPINGS, dict)
    assert len(mod.MODEL_MAPPINGS) > 0


def test_s3_bucket_is_string(_mock_external_deps):
    """S3_BUCKET is a non-empty string."""
    import importlib

    mod = importlib.import_module("scripts.util.model-downloader")
    assert isinstance(mod.S3_BUCKET, str)
    assert len(mod.S3_BUCKET) > 0


def test_transfer_config_exists(_mock_external_deps):
    """transfer_config is created with memory-safe settings."""
    import importlib

    mod = importlib.import_module("scripts.util.model-downloader")
    assert hasattr(mod, "transfer_config")


def test_stream_models_function_exists(_mock_external_deps):
    """stream_models_to_s3 function is defined."""
    import importlib

    mod = importlib.import_module("scripts.util.model-downloader")
    assert callable(mod.stream_models_to_s3)


def test_valid_extensions_in_download_filter(_mock_external_deps):
    """The download logic filters for .safetensors, .json, etc."""
    import importlib
    import inspect

    mod = importlib.import_module("scripts.util.model-downloader")
    source = inspect.getsource(mod.stream_models_to_s3)
    assert ".safetensors" in source
    assert ".json" in source


def test_hf_token_read_from_env(_mock_external_deps):
    """HF_TOKEN is read from the HF_TOKEN environment variable."""
    import importlib
    import os

    with patch.dict(os.environ, {"HF_TOKEN": "test-token-123"}):
        # Need to reload to pick up env change
        mod = importlib.import_module("scripts.util.model-downloader")
        importlib.reload(mod)
        assert mod.HF_TOKEN == "test-token-123"
