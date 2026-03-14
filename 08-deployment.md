# Deployment

## 1. Local Only (Default)

By default, the app binds to `0.0.0.0:8000` and is accessible:
- From the same PC: `http://localhost:8000`
- From any device on the same WiFi: `http://<pc-local-ip>:8000`

This is sufficient for home use where your tablet is on the same network as your PC.

**Find your PC's local IP:**
```bash
# Linux
ip addr show | grep 'inet ' | grep -v '127.0.0.1'

# macOS
ipconfig getifaddr en0

# Windows
ipconfig | findstr IPv4
```

---

## 2. Remote Access via Cloudflare Tunnel (Recommended)

Cloudflare Tunnel lets you access your local app from anywhere — when you're away from home, or from a mobile network — without opening firewall ports or setting up a VPN.

### 2.1 How It Works

```
Your Android (anywhere)
        │  HTTPS
        ▼
Cloudflare Edge (global CDN)
        │  encrypted tunnel
        ▼
cloudflared daemon (running on your PC)
        │  localhost
        ▼
pdf2cbz backend (:8000)
```

The `cloudflared` daemon running on your PC initiates an outbound connection to Cloudflare — no inbound firewall rules needed.

### 2.2 Setup

**Step 1: Install cloudflared**

```bash
# Linux (Debian/Ubuntu)
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb

# macOS
brew install cloudflare/cloudflare/cloudflared

# Windows
winget install --id Cloudflare.cloudflared
```

**Step 2: Log in to Cloudflare**

```bash
cloudflared tunnel login
# Opens browser, log in to your Cloudflare account (free tier is fine)
```

**Step 3: Create a named tunnel**

```bash
cloudflared tunnel create pdf2cbz
# Outputs a tunnel UUID, e.g. a1b2c3d4-e5f6-...
```

**Step 4: Configure the tunnel**

Create `~/.cloudflared/config.yml`:

```yaml
tunnel: a1b2c3d4-e5f6-...        # your tunnel UUID
credentials-file: /home/yourname/.cloudflared/a1b2c3d4-e5f6-....json

ingress:
  - hostname: pdf2cbz.yourdomain.com
    service: http://localhost:8000
  - service: http_status:404
```

If you don't have a domain, use a quick tunnel instead (Step 5b).

**Step 5a: With your own domain**

Add a DNS CNAME record in Cloudflare dashboard:
```
pdf2cbz.yourdomain.com  →  CNAME  →  a1b2c3d4-e5f6-....cfargotunnel.com
```

Then run:
```bash
cloudflared tunnel run pdf2cbz
```

Your app is now at `https://pdf2cbz.yourdomain.com`.

**Step 5b: Without a domain (quick tunnel)**

```bash
cloudflared tunnel --url http://localhost:8000
# Outputs a random URL like https://randomly-named.trycloudflare.com
# This URL changes every time you run it
```

### 2.3 Run on Startup (Linux systemd)

```bash
sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

### 2.4 Security Considerations

When your app is publicly accessible via a tunnel:

- Anyone who knows the URL can access it — Cloudflare Tunnel has no authentication by default
- For a personal tool, using a **long random subdomain** (obscurity) is usually sufficient
- For stronger security, add **Cloudflare Access** (free tier: 50 users) to require Google/GitHub login before the app loads
- Your PC must be running and `cloudflared` must be active for the app to be reachable
- PDF content never transits Cloudflare unencrypted — the tunnel uses TLS end-to-end

### 2.5 Cloudflare Access (Optional, Zero-Trust Auth)

If you want to require authentication:

1. Go to Cloudflare Zero Trust dashboard → Access → Applications
2. Add application → Self-hosted
3. Set domain to `pdf2cbz.yourdomain.com`
4. Add policy: Allow email = your email address
5. Choose identity provider: Google, GitHub, or one-time PIN (no account needed)

Now anyone hitting your URL must authenticate with your email before they can use the app.

---

## 3. Docker Compose (Optional Isolation)

For a cleaner setup or to run the app without polluting your system Python:

**`docker-compose.yml`:**

```yaml
version: '3.8'

services:
  pdf2cbz:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ${HOME}/pdf2cbz/projects:/data/projects   # persist projects
      - ${HOME}/.cache/huggingface:/root/.cache/huggingface  # persist model weights
    environment:
      - PDF2CBZ_PROJECTS_DIR=/data/projects
      - PDF2CBZ_HOST=0.0.0.0
      - PDF2CBZ_PORT=8000
    restart: unless-stopped
```

**`Dockerfile`:**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# System dependencies for PyMuPDF and OpenCV
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download surya model weights into the image layer
RUN python -c "from surya.model.layout.encoderdecoder import LayoutEncoderDecoder; \
               LayoutEncoderDecoder.from_pretrained('vikp/surya_layout3')"

# Frontend build
COPY frontend/package*.json frontend/
RUN cd frontend && npm ci

COPY . .
RUN cd frontend && npm run build

EXPOSE 8000
CMD ["python", "app.py"]
```

**Run:**
```bash
docker-compose up -d
# App at http://localhost:8000
```

> Note: The Docker image will be large (~4 GB) due to PyTorch and surya model weights. Build once, run always.

---

## 4. Optional VPS Deployment

If you want the app running 24/7 without your PC needing to be on, a small VPS works well.

**Recommended:** Hetzner CAX11 (ARM64, 2 vCPU, 4 GB RAM, 40 GB SSD) — ~€4/month

### Setup on VPS

```bash
# On the VPS
git clone https://github.com/yourname/pdf2cbz
cd pdf2cbz

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python scripts/download_models.py

cd frontend && npm install && npm run build && cd ..

# Run with systemd (see below)
```

**`/etc/systemd/system/pdf2cbz.service`:**

```ini
[Unit]
Description=PDF2CBZ
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/home/youruser/pdf2cbz
ExecStart=/home/youruser/pdf2cbz/venv/bin/python app.py
Restart=on-failure
Environment=PDF2CBZ_HOST=127.0.0.1
Environment=PDF2CBZ_OPEN_BROWSER=false

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable pdf2cbz
sudo systemctl start pdf2cbz
```

Put nginx in front for HTTPS (use Certbot for free TLS):

```nginx
server {
    listen 443 ssl;
    server_name pdf2cbz.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/pdf2cbz.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/pdf2cbz.yourdomain.com/privkey.pem;

    client_max_body_size 310M;   # allow 300MB uploads

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_read_timeout 300s;   # allow long-running detection/export
    }
}
```

> **Caveat:** surya detection on a 2-core ARM VPS will be significantly slower than on your own PC (30–60s per page). Consider using the OpenCV fallback for VPS deployments.

---

## 5. Deployment Comparison

| Option | Cost | Setup | Processing Speed | Always On | Best For |
|---|---|---|---|---|---|
| Local only | Free | None | Fast (your PC) | No | Home WiFi use |
| Cloudflare Tunnel | Free | 15 min | Fast (your PC) | When PC is on | Away from home |
| VPS (Hetzner CAX11) | ~€4/mo | 1 hour | Slow (weak CPU) | Yes | Always-available |
| Docker (local) | Free | 30 min | Fast (your PC) | When PC is on | Clean isolation |
