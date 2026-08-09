"""Tests for runner.run_playbook() — the function that either simulates
playbook output (DEMO_MODE) or actually shells out to ansible-playbook.

We mock subprocess.run everywhere so these tests run anywhere (CI included)
without needing real SSH-reachable fleet nodes.
"""
import os
import sys
import subprocess

APP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app")
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

import runner


def test_demo_mode_returns_known_playbook_output(monkeypatch):
    monkeypatch.setattr(runner, "DEMO_MODE", True)

    result = runner.run_playbook("service_check")

    assert result["success"] is True
    assert result["output"].startswith("[DEMO MODE]")
    assert "sshd status: active" in result["output"]


def test_demo_mode_falls_back_for_unknown_playbook(monkeypatch):
    monkeypatch.setattr(runner, "DEMO_MODE", True)

    result = runner.run_playbook("something_not_defined")

    assert result["success"] is True
    assert "something_not_defined completed." in result["output"]


def test_real_mode_missing_playbook_file_fails_cleanly(monkeypatch, tmp_path):

    monkeypatch.setattr(runner, "DEMO_MODE", False)
    monkeypatch.setattr(runner, "PLAYBOOK_DIR", str(tmp_path))

    result = runner.run_playbook("service_check")

    assert result["success"] is False
    assert "Playbook not found" in result["output"]


def test_real_mode_success_returns_stdout(monkeypatch, tmp_path):
    monkeypatch.setattr(runner, "DEMO_MODE", False)
    playbook_dir = tmp_path / "playbooks"
    playbook_dir.mkdir()
    (playbook_dir / "service_check.yml").write_text("---\n- hosts: all\n")
    monkeypatch.setattr(runner, "PLAYBOOK_DIR", str(playbook_dir))

    fake_result = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="PLAY RECAP node1 : ok=1", stderr=""
    )
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: fake_result)

    result = runner.run_playbook("service_check")

    assert result["success"] is True
    assert "PLAY RECAP" in result["output"]


def test_real_mode_failure_includes_stderr(monkeypatch, tmp_path):

    monkeypatch.setattr(runner, "DEMO_MODE", False)
    playbook_dir = tmp_path / "playbooks"
    playbook_dir.mkdir()
    (playbook_dir / "create_user.yml").write_text("---\n- hosts: all\n")
    monkeypatch.setattr(runner, "PLAYBOOK_DIR", str(playbook_dir))

    fake_result = subprocess.CompletedProcess(
        args=[], returncode=2, stdout="", stderr="fatal: [node2]: UNREACHABLE!"
    )
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: fake_result)

    result = runner.run_playbook("create_user")

    assert result["success"] is False
    assert "UNREACHABLE" in result["output"]


def test_real_mode_calls_ansible_playbook_with_correct_args(monkeypatch, tmp_path):
    
    monkeypatch.setattr(runner, "DEMO_MODE", False)
    playbook_dir = tmp_path / "playbooks"
    playbook_dir.mkdir()
    (playbook_dir / "log_rotate.yml").write_text("---\n- hosts: all\n")
    monkeypatch.setattr(runner, "PLAYBOOK_DIR", str(playbook_dir))
    monkeypatch.setattr(runner, "INVENTORY_PATH", "/fake/inventory.ini")

    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    runner.run_playbook("log_rotate")

    assert captured["cmd"][0] == "ansible-playbook"
    assert "-i" in captured["cmd"]
    assert "/fake/inventory.ini" in captured["cmd"]
    assert str(playbook_dir / "log_rotate.yml") in captured["cmd"]
