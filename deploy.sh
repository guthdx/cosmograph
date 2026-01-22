#!/bin/bash
# Cosmograph deployment script for Iyeska HQ (192.168.11.20)
set -e

cd /home/guthdx/projects/cosmograph

echo "=== Pulling latest code ==="
git pull origin main

echo "=== Updating Python dependencies ==="
source .venv/bin/activate
pip install -e ".[all]"

echo "=== Building frontend ==="
cd frontend
npm ci
npm run build
cd ..

echo "=== Restarting PM2 process ==="
pm2 restart cosmograph --update-env

echo "=== Deployment complete ==="
echo "Check status: pm2 status cosmograph"
echo "Check logs: pm2 logs cosmograph"
echo "Health check: curl http://localhost:8003/health"
