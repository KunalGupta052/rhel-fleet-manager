import os
import subprocess
import random

# When DEMO_MODE=1 (set this on hosted platforms like Render that have no
# real fleet of SSH-reachable nodes), we simulate playbook output instead
# of shelling out to ansible-playbook. Locally, leave DEMO_MODE unset to
# run against your real Docker-based nodes.
DEMO_MODE = os.environ.get("DEMO_MODE", "0") == "1"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INVENTORY_PATH = os.path.join(BASE_DIR, "ansible", "inventory.ini")
PLAYBOOK_DIR = os.path.join(BASE_DIR, "ansible", "playbooks")

_DEMO_OUTPUTS = {
    "service_check": "node1 - sshd status: active\nnode2 - sshd status: active",
    "create_user": "node1 - user 'opsuser' present: True\nnode2 - user 'opsuser' present: True",
    "install_package": "node1 - package 'htop' status: True\nnode2 - package 'htop' status: True",
    "log_rotate": "node1 - removed 3 log file(s) older than 7 days\nnode2 - removed 1 log file(s) older than 7 days",
}


def run_playbook(playbook_name: str) -> dict:
    """Runs an Ansible playbook by name (without .yml) and returns
    {"success": bool, "output": str}.
    """
    if DEMO_MODE:
        # Simulate a short delay-free "success" run with realistic sample output.
        output = _DEMO_OUTPUTS.get(playbook_name, f"{playbook_name} completed.")
        return {"success": True, "output": f"[DEMO MODE]\n{output}"}

    playbook_path = os.path.join(PLAYBOOK_DIR, f"{playbook_name}.yml")
    if not os.path.exists(playbook_path):
        return {"success": False, "output": f"Playbook not found: {playbook_path}"}

    result = subprocess.run(
        ["ansible-playbook", "-i", INVENTORY_PATH, playbook_path],
        capture_output=True,
        text=True,
    )
    output = result.stdout + ("\n" + result.stderr if result.returncode != 0 else "")
    return {"success": result.returncode == 0, "output": output}
