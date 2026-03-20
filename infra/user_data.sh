#!/bin/bash
set -euo pipefail

# Guard : ne s'exécute qu'une seule fois (pas au reboot)
LOCK_FILE="/var/log/user_data.done"
if [ -f "$LOCK_FILE" ]; then
  echo "Bootstrap déjà effectué, skip."
  exit 0
fi

exec > /var/log/user_data.log 2>&1

echo "=== [1/6] Mise à jour système ==="
apt-get update -y
apt-get install -y ca-certificates curl gnupg git

echo "=== [2/6] Swap 2GB (évite OOM sur t3.micro) ==="
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab

echo "=== [3/6] Installation Docker ==="
curl -fsSL https://get.docker.com | sh
usermod -aG docker ubuntu
systemctl enable docker
systemctl start docker

echo "=== [4/6] Clone du repo ==="
git clone https://github.com/francklebas/jobboard.git /home/ubuntu/jobboard
chown -R ubuntu:ubuntu /home/ubuntu/jobboard

echo "=== [5/6] Démarrage docker compose ==="
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)

cd /home/ubuntu/jobboard
cat > /home/ubuntu/jobboard/.env <<EOF
POSTGRES_DB=${postgres_db}
POSTGRES_USER=${postgres_user}
POSTGRES_PASSWORD=${postgres_password}
DATABASE_URL=postgresql+psycopg2://${postgres_user}:${postgres_password}@postgres:5432/${postgres_db}
SCRAPE_INTERVAL_HOURS=${scrape_interval}
NUXT_PUBLIC_API_URL=http://$${PUBLIC_IP}:8000
NITRO_API_URL=http://api:8000
EOF

chown ubuntu:ubuntu /home/ubuntu/jobboard/.env
chmod 600 /home/ubuntu/jobboard/.env

docker compose up -d --build

echo "=== [6/6] Crontab scrape toutes les 6h ==="
(crontab -u ubuntu -l 2>/dev/null || true; echo "0 */${scrape_interval} * * * curl -s -X POST http://localhost:8000/jobs/sync") | crontab -u ubuntu -

touch "$LOCK_FILE"
echo "=== Bootstrap termine - IP publique : $${PUBLIC_IP} ==="
