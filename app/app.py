import os
from flask import Flask, jsonify, render_template
from models import db, RunLog
from runner import run_playbook

app = Flask(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fleet.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

AVAILABLE_PLAYBOOKS = [
    {"id": "service_check", "label": "Check sshd Service"},
    {"id": "create_user", "label": "Create Ops User"},
    {"id": "install_package", "label": "Install htop Package"},
    {"id": "log_rotate", "label": "Rotate Old Logs"},
]


@app.route("/")
def dashboard():
    logs = RunLog.query.order_by(RunLog.timestamp.desc()).limit(20).all()
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


@app.route("/logs")
def logs_json():
    logs = RunLog.query.order_by(RunLog.timestamp.desc()).limit(20).all()
    return jsonify([log.to_dict() for log in logs])


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
