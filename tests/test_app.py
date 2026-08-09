"""Tests for the Flask routes in app.py."""

def test_dashboard_loads(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"RHEL Fleet Manager" in resp.data


def test_trigger_rejects_unknown_playbook(client):
    resp = client.get("/run/not-a-real-playbook")

    assert resp.status_code == 400
    body = resp.get_json()
    assert body["success"] is False
    assert body["output"] == "Unknown playbook"


def test_trigger_valid_playbook_logs_success(client, app, monkeypatch):
    monkeypatch.setattr("app.run_playbook", lambda name: {"success": True, "output": "mocked ok"})

    resp = client.get("/run/service_check")

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert body["output"] == "mocked ok"
    assert "id" in body
    assert "timestamp" in body

    with app.app_context():
        from models import RunLog
        logs = RunLog.query.all()
        assert len(logs) == 1
        assert logs[0].playbook == "service_check"
        assert logs[0].status == "success"
        assert logs[0].output == "mocked ok"


def test_trigger_failed_playbook_logs_failed_status(client, app, monkeypatch):
    monkeypatch.setattr("app.run_playbook", lambda name: {"success": False, "output": "node2 unreachable"})

    resp = client.get("/run/create_user")

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is False

    with app.app_context():
        from models import RunLog
        entry = RunLog.query.first()
        assert entry.status == "failed"
        assert entry.output == "node2 unreachable"


def test_logs_endpoint_returns_most_recent_first(client, app, monkeypatch):
    monkeypatch.setattr("app.run_playbook", lambda name: {"success": True, "output": "ok"})

    client.get("/run/service_check")
    client.get("/run/create_user")

    resp = client.get("/logs")

    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) == 2
    # create_user ran second, so it should come back first (most recent first)
    assert data[0]["playbook"] == "create_user"
    assert data[1]["playbook"] == "service_check"


def test_logs_endpoint_caps_at_twenty(client, app, monkeypatch):
    monkeypatch.setattr("app.run_playbook", lambda name: {"success": True, "output": "ok"})

    for _ in range(25):
        client.get("/run/service_check")

    resp = client.get("/logs")
    data = resp.get_json()

    assert len(data) == 20
