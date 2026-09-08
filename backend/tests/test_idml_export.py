import os
import subprocess

import pytest

from babel.idml.export import convert_to_idml, ConvertResult, export, ExportResult


def test_convert_to_idml_no_server_configured(monkeypatch, tmp_path):
    monkeypatch.delenv("INDESIGN_SERVER", raising=False)
    result = convert_to_idml(str(tmp_path / "in.indd"), str(tmp_path / "out"))
    assert result.ok is False
    assert result.idml is None
    assert "INDESIGN_SERVER" in result.message


def test_convert_to_idml_server_path_missing(monkeypatch, tmp_path):
    monkeypatch.setenv("INDESIGN_SERVER", str(tmp_path / "nonexistent-binary"))
    result = convert_to_idml(str(tmp_path / "in.indd"), str(tmp_path / "out"))
    assert result.ok is False
    assert "not found" in result.message


def test_convert_to_idml_success(monkeypatch, tmp_path):
    server = tmp_path / "InDesignServer"
    server.write_text("#!/bin/sh\n")
    monkeypatch.setenv("INDESIGN_SERVER", str(server))

    def fake_run(cmd, capture_output, text, timeout):
        assert cmd[0] == str(server)
        assert "-script" in cmd
        assert any("inddPath=" in a for a in cmd)
        assert any("idmlPath=" in a for a in cmd)
        return subprocess.CompletedProcess(cmd, returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    out_dir = str(tmp_path / "out")
    result = convert_to_idml(str(tmp_path / "in.indd"), out_dir)
    assert result.ok is True
    assert result.idml == os.path.abspath(os.path.join(out_dir, "in.idml"))
    assert isinstance(result, ConvertResult)


def test_convert_to_idml_server_error(monkeypatch, tmp_path):
    server = tmp_path / "InDesignServer"
    server.write_text("#!/bin/sh\n")
    monkeypatch.setenv("INDESIGN_SERVER", str(server))

    def fake_run(cmd, capture_output, text, timeout):
        return subprocess.CompletedProcess(cmd, returncode=1, stdout="", stderr="boom")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = convert_to_idml(str(tmp_path / "in.indd"), str(tmp_path / "out"))
    assert result.ok is False
    assert "boom" in result.message


def test_export_no_server_configured(monkeypatch, tmp_path):
    monkeypatch.delenv("INDESIGN_SERVER", raising=False)
    result = export(str(tmp_path / "in.idml"), str(tmp_path / "out"))
    assert result.ok is False
    assert result.indd is None
    assert not hasattr(result, "pdf")


def test_export_success_indd_only(monkeypatch, tmp_path):
    server = tmp_path / "InDesignServer"
    server.write_text("#!/bin/sh\n")
    monkeypatch.setenv("INDESIGN_SERVER", str(server))

    def fake_run(cmd, capture_output, text, timeout):
        assert not any("pdfPath=" in a for a in cmd)
        return subprocess.CompletedProcess(cmd, returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    out_dir = str(tmp_path / "out")
    result = export(str(tmp_path / "in.idml"), out_dir)
    assert result.ok is True
    assert result.indd == os.path.abspath(os.path.join(out_dir, "in.indd"))
    assert isinstance(result, ExportResult)
