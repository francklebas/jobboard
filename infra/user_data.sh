#!/bin/bash
set -euo pipefail

# Guard : ne s'exécute qu'une seule fois (pas au reboot)
LOCK_FILE="/var/log/user_data.done"
if [ -f "$LOCK_FILE" ]; then
  echo "Bootstrap déjà effectué, skip."
  exit 0
fi

exec > /var/log/user_data.log 2>&1

echo "=== [1/5] Mise à jour système ==="
apt-get update -y
apt-get install -y ca-certificates curl gnupg git

echo "=== [2/5] Installation Docker ==="
curl -fsSL https://get.docker.com | sh
usermod -aG docker ubuntu
systemctl enable docker
systemctl start docker

echo "=== [3/5] Clone du repo ==="
git clone https://github.com/francklebas/jobboard.git /home/ubuntu/jobboard
chown -R ubuntu:ubuntu /home/ubuntu/jobboard

echo "=== [4/5] Démarrage docker compose ==="
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)

cd /home/ubuntu/jobboard
NUXT_PUBLIC_API_URL="http://${PUBLIC_IP}:8000" \
NITRO_API_URL="http://api:8000" \
sudo -u ubuntu docker compose up -d --build

echo "=== [5/5] Crontab scrape toutes les 6h ==="
(crontab -u ubuntu -l 2>/dev/null; echo "0 */6 * * * curl -s -X POST http://localhost:8000/jobs/sync") | crontab -u ubuntu -

touch "$LOCK_FILE"
echo "=== Bootstrap terminé — IP publique : ${PUBLIC_IP} ==="
