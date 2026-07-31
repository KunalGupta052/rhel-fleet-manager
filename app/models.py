from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class RunLog(db.Model):
    """Stores the result of every Ansible playbook run triggered from the dashboard."""

    id = db.Column(db.Integer, primary_key=True)
    playbook = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), nullable=False)   # success | failed
    output = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "playbook": self.playbook,
            "status": self.status,
            "output": self.output,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S") if self.timestamp else None,
        }
