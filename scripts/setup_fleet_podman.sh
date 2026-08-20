#!/bin/bash
# Automate local multi-node RHEL/CentOS fleet setup using Podman on RHEL 9
set -euo pipefail

IMAGE="quay.io/rockylinux/rockylinux:9"
NET="rhel-fleet-net"

echo "==> Configuring Podman Network..."
podman network exists $NET || podman network create $NET

for NODE in node1 node2; do
  PORT=$([ "$NODE" == "node1" ] && echo 2221 || echo 2222)
  echo "==> Deploying $NODE on port $PORT..."
  podman rm -f "$NODE" 2>/dev/null || true
  
  podman run -d \
    --name "$NODE" \
    --network "$NET" \
    -p "$PORT:22" \
    --systemd=always \
    "$IMAGE" /sbin/init

  echo "==> Setting up SSH and Ansible user in $NODE..."
  podman exec "$NODE" dnf install -y openssh-server python3 sudo
  podman exec "$NODE" systemctl enable --now sshd
  podman exec "$NODE" useradd -m -s /bin/bash ansible
  podman exec "$NODE" bash -c "echo 'ansible:ansible123' | chpasswd"
  podman exec "$NODE" bash -c "echo 'ansible ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/ansible"
done

echo "==> Fleet is ready. Testing connection:"
ansible -i ansible/inventory.ini fleet -m ping
