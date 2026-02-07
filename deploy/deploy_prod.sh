#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_DIR="/var/www/Front_liner"
BRANCH="${1:-main}"

echo "[deploy] project_dir=${PROJECT_DIR} branch=${BRANCH}"
cd "${PROJECT_DIR}"

echo "[deploy] syncing git branch"
git fetch origin "${BRANCH}"
git checkout "${BRANCH}"
git pull --ff-only origin "${BRANCH}"

if [ ! -d "${PROJECT_DIR}/venv" ]; then
  echo "[deploy] creating venv"
  python3 -m venv "${PROJECT_DIR}/venv"
fi

echo "[deploy] installing dependencies"
source "${PROJECT_DIR}/venv/bin/activate"
pip install --upgrade pip
pip install -r requirements.txt

echo "[deploy] applying migrations and collecting static files"
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py check

echo "[deploy] restarting services"
sudo systemctl restart frontliner-gunicorn
sudo systemctl reload nginx

echo "[deploy] done"
