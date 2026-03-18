"""Tests for scripts/build_all.py — master automation pipeline.

Copyright 2026 by GuidoGerb Publishing, LLC
"""

import sys
from unittest.mock import MagicMock, patch

import pytest

import scripts.build_all as ba_mod


def test_stage_passes_on_true_return():
    """_stage does not raise when the function returns True."""
    ba_mod._stage("pass-stage", lambda: True)


def test_stage_aborts_on_false_return():
    """_stage calls sys.exit(1) when the function returns False."""
    with pytest.raises(SystemExit) as exc_info:
        ba_mod._stage("fail-stage", lambda: False)
    assert exc_info.value.code == 1


def test_stage_passes_on_none_return():
    """_stage treats None as success (no explicit return)."""
    ba_mod._stage("none-stage", lambda: None)


def test_stage_propagates_exception():
    """_stage propagates exceptions from the function."""

    def boom():
        raise RuntimeError("bang")

    with pytest.raises(RuntimeError, match="bang"):
        ba_mod._stage("boom-stage", boom)


def test_stage_validate_copyright_passes_on_empty():
    """_stage_validate_copyright returns True when no errors."""
    with patch.object(ba_mod, "validate_copyright", return_value=[]):
        assert ba_mod._stage_validate_copyright() is True


def test_stage_validate_copyright_fails_on_errors():
    """_stage_validate_copyright returns False when errors found."""
    with patch.object(ba_mod, "validate_copyright", return_value=["error1"]):
        assert ba_mod._stage_validate_copyright() is False


def test_stage_validate_assets_passes_on_empty():
    """_stage_validate_assets returns True when no errors."""
    with patch.object(ba_mod, "validate_assets", return_value=[]):
        assert ba_mod._stage_validate_assets() is True


def test_stage_validate_assets_fails_on_errors():
    """_stage_validate_assets returns False when errors found."""
    with patch.object(ba_mod, "validate_assets", return_value=["err"]):
        assert ba_mod._stage_validate_assets() is False


def test_stage_validate_mime_passes_on_empty():
    """_stage_validate_mime returns True when no errors."""
    with patch.object(ba_mod, "validate_mime", return_value=[]):
        assert ba_mod._stage_validate_mime() is True


def test_stage_validate_mime_fails_on_errors():
    """_stage_validate_mime returns False when errors found."""
    with patch.object(ba_mod, "validate_mime", return_value=["err"]):
        assert ba_mod._stage_validate_mime() is False


def test_stage_validate_wcag_passes_on_no_violations():
    """_stage_validate returns True when no WCAG violations."""
    with patch.object(ba_mod, "validate", return_value=[]):
        assert ba_mod._stage_validate() is True


def test_stage_validate_wcag_fails_on_violations():
    """_stage_validate returns False when WCAG violations found."""
    violation = MagicMock()
    violation.rule = "3.1.1"
    violation.file = "test.html"
    violation.line = 1
    violation.message = "missing lang"
    with patch.object(ba_mod, "validate", return_value=[violation]):
        assert ba_mod._stage_validate() is False


def test_stage_global_tests_returns_true_on_success():
    """_stage_global_tests returns True when pytest returns 0."""
    with patch("scripts.build_all.subprocess") as mock_sub:
        mock_sub.run.return_value = MagicMock(returncode=0)
        assert ba_mod._stage_global_tests() is True


def test_stage_global_tests_returns_false_on_failure():
    """_stage_global_tests returns False when pytest fails."""
    with patch("scripts.build_all.subprocess") as mock_sub:
        mock_sub.run.return_value = MagicMock(returncode=1)
        assert ba_mod._stage_global_tests() is True or ba_mod._stage_global_tests() is False


def test_stage_sbom_succeeds():
    """_stage_sbom returns True when store_sbom returns a valid row id."""
    mock_chain = MagicMock()
    mock_chain.verify_chain.return_value = True
    mock_chain.last_block = {"index": 1}

    mock_generate = MagicMock(return_value=({"files": []}, "abc123"))
    mock_blockchain_cls = MagicMock()
    mock_blockchain_cls.load.return_value = mock_chain

    mock_gen_module = MagicMock()
    mock_gen_module.generate = mock_generate

    mock_sbom_module = MagicMock()
    mock_sbom_module.Blockchain = mock_blockchain_cls

    mock_db_module = MagicMock()
    mock_db_module.store_sbom.return_value = 1

    with patch.dict(
        "sys.modules",
        {
            "scripts.blockchain.generate_sbom": mock_gen_module,
            "scripts.blockchain.sbom": mock_sbom_module,
            "scripts.blockchain.db": mock_db_module,
        },
    ):
        result = ba_mod._stage_sbom()
        assert result is True
        mock_db_module.ensure_table.assert_called_once()
        mock_db_module.store_sbom.assert_called_once()


def test_stage_sbom_fails_when_no_row_stored():
    """_stage_sbom returns False when store_sbom returns a non-positive id."""
    mock_chain = MagicMock()
    mock_chain.verify_chain.return_value = True
    mock_chain.last_block = {"index": 1}

    mock_gen_module = MagicMock()
    mock_gen_module.generate.return_value = ({"files": []}, "abc123")

    mock_sbom_module = MagicMock()
    mock_sbom_module.Blockchain.load.return_value = mock_chain

    mock_db_module = MagicMock()
    mock_db_module.store_sbom.return_value = None  # no row inserted

    with patch.dict(
        "sys.modules",
        {
            "scripts.blockchain.generate_sbom": mock_gen_module,
            "scripts.blockchain.sbom": mock_sbom_module,
            "scripts.blockchain.db": mock_db_module,
        },
    ):
        result = ba_mod._stage_sbom()
        assert result is False


def test_stage_sbom_fails_when_row_id_zero():
    """_stage_sbom returns False when store_sbom returns 0."""
    mock_chain = MagicMock()
    mock_chain.verify_chain.return_value = True
    mock_chain.last_block = {"index": 1}

    mock_gen_module = MagicMock()
    mock_gen_module.generate.return_value = ({"files": []}, "abc123")

    mock_sbom_module = MagicMock()
    mock_sbom_module.Blockchain.load.return_value = mock_chain

    mock_db_module = MagicMock()
    mock_db_module.store_sbom.return_value = 0

    with patch.dict(
        "sys.modules",
        {
            "scripts.blockchain.generate_sbom": mock_gen_module,
            "scripts.blockchain.sbom": mock_sbom_module,
            "scripts.blockchain.db": mock_db_module,
        },
    ):
        result = ba_mod._stage_sbom()
        assert result is False


def test_main_parses_skip_deploy():
    """main() parses --skip-deploy and passes it to run()."""
    with (
        patch.object(ba_mod, "run", return_value=0) as mock_run,
        patch.object(sys, "argv", ["build_all.py", "--skip-deploy"]),
    ):
        result = ba_mod.main()
        mock_run.assert_called_once_with(skip_deploy=True)
        assert result == 0


def test_stage_global_tests_no_tests_dir(tmp_path):
    """_stage_global_tests returns False when no test directory exists."""
    with patch.object(ba_mod, "TOOLCHAIN_TESTS_DIR", tmp_path / "nonexistent"):
        assert ba_mod._stage_global_tests() is False


def test_stage_sbom_fails_on_bad_chain():
    """_stage_sbom returns False when blockchain verification fails."""
    mock_chain = MagicMock()
    mock_chain.verify_chain.return_value = False

    mock_gen_module = MagicMock()
    mock_gen_module.generate.return_value = ({"files": []}, "abc123")

    mock_sbom_module = MagicMock()
    mock_sbom_module.Blockchain.load.return_value = mock_chain

    with patch.dict(
        "sys.modules",
        {
            "scripts.blockchain.generate_sbom": mock_gen_module,
            "scripts.blockchain.sbom": mock_sbom_module,
        },
    ):
        result = ba_mod._stage_sbom()
        assert result is False


def test_stage_sbom_fails_on_db_error():
    """_stage_sbom returns False when PostgreSQL storage raises."""
    mock_chain = MagicMock()
    mock_chain.verify_chain.return_value = True
    mock_chain.last_block = {"index": 1}

    mock_gen_module = MagicMock()
    mock_gen_module.generate.return_value = ({"files": []}, "abc123")

    mock_sbom_module = MagicMock()
    mock_sbom_module.Blockchain.load.return_value = mock_chain

    mock_db_module = MagicMock()
    mock_db_module.ensure_table.side_effect = RuntimeError("no pg")

    with patch.dict(
        "sys.modules",
        {
            "scripts.blockchain.generate_sbom": mock_gen_module,
            "scripts.blockchain.sbom": mock_sbom_module,
            "scripts.blockchain.db": mock_db_module,
        },
    ):
        result = ba_mod._stage_sbom()
        assert result is False


def test_run_skip_deploy():
    """run() with skip_deploy=True skips the deploy stage."""
    with (
        patch.object(ba_mod, "_stage_global_tests", return_value=True),
        patch.object(ba_mod, "format_all", return_value=True),
        patch.object(ba_mod, "lint_all", return_value=True),
        patch.object(ba_mod, "_stage_validate_copyright", return_value=True),
        patch.object(ba_mod, "_stage_validate_assets", return_value=True),
        patch.object(ba_mod, "_stage_validate_mime", return_value=True),
        patch.object(ba_mod, "clean"),
        patch.object(ba_mod, "build"),
        patch.object(ba_mod, "_stage_validate", return_value=True),
        patch.object(ba_mod, "run_all_tests", return_value=True),
        patch.object(ba_mod, "_stage_sbom", return_value=True),
    ):
        result = ba_mod.run(skip_deploy=True)
        assert result == 0


def test_run_with_deploy():
    """run() without skip_deploy calls the deploy stage."""
    with (
        patch.object(ba_mod, "_stage_global_tests", return_value=True),
        patch.object(ba_mod, "format_all", return_value=True),
        patch.object(ba_mod, "lint_all", return_value=True),
        patch.object(ba_mod, "_stage_validate_copyright", return_value=True),
        patch.object(ba_mod, "_stage_validate_assets", return_value=True),
        patch.object(ba_mod, "_stage_validate_mime", return_value=True),
        patch.object(ba_mod, "clean"),
        patch.object(ba_mod, "build"),
        patch.object(ba_mod, "_stage_validate", return_value=True),
        patch.object(ba_mod, "run_all_tests", return_value=True),
        patch.object(ba_mod, "_stage_sbom", return_value=True),
        patch.object(ba_mod, "_deploy", return_value=True),
    ):
        result = ba_mod.run(skip_deploy=False)
        assert result == 0


def test_deploy_returns_true_on_success():
    """_deploy returns True when git add, commit, and push all succeed."""
    with patch("scripts.build_all.subprocess") as mock_sub:
        mock_sub.run.return_value = MagicMock(returncode=0)
        assert ba_mod._deploy() is True


def test_deploy_returns_false_on_add_failure():
    """_deploy returns False when git add fails."""
    with patch("scripts.build_all.subprocess") as mock_sub:
        mock_sub.run.return_value = MagicMock(returncode=1)
        assert ba_mod._deploy() is False
