import os
from flask import Flask, jsonify, render_template
from models import db, RunLog
from runner import run_playbook
from flask import Flask, jsonify, render_template, Response
from models import db, RunLog
from runner import execute_playbook, stream_playbook_logs, AVAILABLE_PLAYBOOKS

AVAILABLE_PLAYBOOKS = [
    {"id": "service_check", "label": "Check sshd Service"},
    {"id": "create_user", "label": "Create Ops User"},
    {"id": "install_package", "label": "Install htop Package"},
    {"id": "log_rotate", "label": "Rotate Old Logs"},
]


def create_app(test_config: dict | None = None) -> Flask:
    """Application factory. Building the app this way (instead of a bare
    module-level Flask() instance) lets tests spin up an isolated app with
    its own in-memory database and TESTING flag, without touching the real
    fleet.db used in development/production."""
    app = Flask(__name__)

    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fleet.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    @app.route("/")
    def dashboard():
        logs = RunLog.query.order_by(RunLog.timestamp.desc(), RunLog.id.desc()).limit(20).all()
        return render_template("dashboard.html", logs=logs, playbooks=AVAILABLE_PLAYBOOKS)

    @app.route("/run/<playbook_id>")
    def trigger(playbook_id):
        valid_ids = {p["id"] for p in AVAILABLE_PLAYBOOKS}
        if playbook_id not in valid_ids:
            return jsonify({"success": False, "output": "Unknown playbook"}), 400

        result = run_playbook(playbook_id)
        entry = RunLog(
            playbook=playbook_id,
            status="success" if result["success"] else "failed",
            output=result["output"],
        )
        db.session.add(entry)
        db.session.commit()
        return jsonify({**result, "id": entry.id, "timestamp": entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")})
    @app.route("/stream/<playbook_name>")
    def stream_run(playbook_name):
        valid_ids = [p["id"] for p in AVAILABLE_PLAYBOOKS]
        if playbook_name not in valid_ids:
            return jsonify({"error": "Invalid playbook"}), 400
        
        return Response(
            stream_playbook_logs(playbook_name),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no"
            }
        )

    @app.route("/logs")
    def logs_json():
        logs = RunLog.query.order_by(RunLog.timestamp.desc(), RunLog.id.desc()).limit(20).all()
        return jsonify([log.to_dict() for log in logs])

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
