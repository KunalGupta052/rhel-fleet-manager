# RHEL Fleet Manager

A lightweight automation dashboard that triggers Ansible playbooks against a fleet of RHEL/CentOS-family servers, logs every run to a database, and shows live status through a web UI.

Built to demonstrate practical Linux system administration + automation + full-stack skills: Ansible, Python, SQL, and a JS-driven frontend, all working together in one deployable app.

**Live demo:** _add your deployed link here_
**Local demo GIF:** _add a screen recording here once you run it locally_

---

## Why this project

Most "sysadmin" portfolio projects are either a pile of shell scripts with no interface, or a to-do-list web app with no real infrastructure behind it. This project sits in between: real Ansible playbooks doing real Linux administration tasks (user management, package installs, service checks, log rotation), triggered and observed through an actual web dashboard, with every run persisted to a database.

## Architecture

```
Browser (dashboard.html)
      │  fetch('/run/<playbook>')
      ▼
Flask app (app.py)
      │  subprocess call
      ▼
ansible-playbook  ──over SSH──►  node1, node2 (fleet)
      │
      ▼
Result logged to SQLite (RunLog table)
      │
      ▼
Dashboard table + toast notification
```

- **Ansible** — playbooks for user creation, package install, service health check, log rotation
- **Python (Flask)** — orchestrates playbook runs via `subprocess`, exposes a small REST-style API
- **SQL (SQLAlchemy + SQLite)** — persists every run: playbook, status, output, timestamp
- **HTML/CSS/JS** — dashboard UI, triggers runs and updates the log table live without a page reload

## Project structure

```
rhel-fleet-manager/
├── ansible/
│   ├── inventory.ini          # fleet node definitions
│   └── playbooks/
│       ├── create_user.yml
│       ├── install_package.yml
│       ├── service_check.yml
│       └── log_rotate.yml
├── app/
│   ├── app.py                 # Flask routes
│   ├── models.py              # SQLAlchemy models
│   ├── runner.py              # subprocess wrapper around ansible-playbook
│   └── templates/
│       └── dashboard.html
├── requirements.txt
├── Procfile                   # for gunicorn-based deployment
└── README.md
```

## Local setup

### 1. Clone and install dependencies
```bash
git clone <your-repo-url>
cd rhel-fleet-manager
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Spin up simulated fleet nodes (Docker)
```bash
docker run -d --name node1 -p 2221:22 rockylinux/rockylinux:9 sleep infinity
docker run -d --name node2 -p 2222:22 rockylinux/rockylinux:9 sleep infinity

# install and start sshd inside each container so Ansible can reach it
docker exec node1 bash -c "dnf install -y openssh-server && ssh-keygen -A && /usr/sbin/sshd"
docker exec node2 bash -c "dnf install -y openssh-server && ssh-keygen -A && /usr/sbin/sshd"
```
Set a root password or copy your SSH key into each container so `ansible_user=root` in `ansible/inventory.ini` can authenticate.

### 3. Verify Ansible can reach the fleet
```bash
ansible -i ansible/inventory.ini fleet -m ping
```

### 4. Run the app
```bash
cd app
python app.py
```
Visit `http://localhost:5000` and click a playbook card to trigger a run — it will show up in the log table instantly.

## Deployment note

Hosted platforms (Render, Railway, etc.) don't have SSH access to real fleet nodes, so this app supports a `DEMO_MODE` environment variable:

```bash
DEMO_MODE=1  # runner.py returns realistic simulated output instead of shelling out to ansible-playbook
```

This keeps the hosted demo fully interactive and honest about what it's doing — set `DEMO_MODE=1` in your hosting platform's environment variables, and leave it unset locally to run against your real Docker-based nodes.

## Possible extensions

- Add authentication so only authorized users can trigger playbooks
- Swap SQLite for PostgreSQL in production
- Add a "diff" view comparing fleet state before/after a run
- Extend playbooks to real cloud VMs instead of local Docker containers

## Tech stack

`Python` · `Flask` · `Ansible` · `SQLAlchemy` · `SQLite` · `HTML/CSS/JS` · `Docker` (for local test nodes)
