# Front_liner VPS Setup (Gunicorn + Nginx)

This project includes Channels/WebSockets, so run Gunicorn in ASGI mode.

## 1) Install system packages

```bash
sudo apt update
sudo apt install -y nginx redis-server
```

## 2) Prepare project environment

```bash
cd /var/www/Front_liner

# If venv is not already created:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run migrations and static collection
python manage.py migrate
python manage.py collectstatic --noinput
```

## 3) Configure Gunicorn service

```bash
sudo cp deploy/frontliner-gunicorn.service /etc/systemd/system/frontliner-gunicorn.service
sudo systemctl daemon-reload
sudo systemctl enable frontliner-gunicorn
sudo systemctl start frontliner-gunicorn
sudo systemctl status frontliner-gunicorn
```

## 4) Configure Nginx

```bash
sudo cp deploy/frontliner-nginx.conf /etc/nginx/sites-available/frontliner
sudo ln -s /etc/nginx/sites-available/frontliner /etc/nginx/sites-enabled/frontliner
sudo nginx -t
sudo systemctl reload nginx
```

## 5) SSL (recommended)

Use Certbot after DNS points to VPS:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d test.frontliner.io
```

## 6) Quick checks

```bash
sudo systemctl status frontliner-gunicorn
sudo systemctl status nginx
tail -f /var/log/frontliner/gunicorn-error.log
```

## Notes

- Gunicorn config file: `deploy/gunicorn.conf.py`
- Systemd service: `deploy/frontliner-gunicorn.service`
- Nginx server block: `deploy/frontliner-nginx.conf`
- If your VPS user/path/domain differs, update these files before copying.

## CI/CD with GitHub Actions

This repo includes:

- Workflow: `.github/workflows/ci-cd.yml`
- Deploy script: `deploy/deploy_prod.sh`

### One-time VPS prep for CI deploy user

1. Ensure code exists at `/var/www/Front_liner` and remote `origin` is configured.
2. Ensure deploy user can run these without password:
3. `sudo systemctl restart frontliner-gunicorn`
4. `sudo systemctl reload nginx`

Example sudoers entry (edit with `sudo visudo`):

```bash
deployuser ALL=(ALL) NOPASSWD:/bin/systemctl restart frontliner-gunicorn,/bin/systemctl reload nginx
```

### GitHub repository secrets

Add these secrets in GitHub repository settings:

- `VPS_HOST` (example: `srv541106` or server public IP)
- `VPS_SSH_KEY` (private key contents)
- `VPS_PORT` (optional, default `22`)

This workflow is configured to SSH as `root`, matching your server prompt:

`root@srv541106:/var/www/Front_liner#`

### Flow

1. On PR to `main`, CI runs Django check + tests.
2. On push to `main`, if CI passes, CD SSHes into VPS and runs:
3. `bash /var/www/Front_liner/deploy/deploy_prod.sh main`
