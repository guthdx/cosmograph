# Phase 7: Deployment - Research

**Researched:** 2026-01-22
**Domain:** Production deployment to Iyeska HQ infrastructure
**Confidence:** HIGH

## Summary

Phase 7 deploys Cosmograph to the Iyeska HQ Ubuntu server (192.168.11.20), making it accessible at https://cosmograph.iyeska.net. The deployment follows established Iyeska patterns: PM2 for process management, Cloudflare Tunnel for public access, and FastAPI serving both API and static frontend files.

The research confirms:
1. PM2 ecosystem.config.js pattern is already proven with wowasi_ya on the same server
2. Cloudflare Tunnel (not Traefik) is the production ingress method for public domains
3. FastAPI can serve the Vite build output via StaticFiles mount (consolidating frontend and backend)
4. Port 8003 is available for cosmograph on the production server

**Primary recommendation:** Deploy as a single PM2-managed FastAPI process serving both API and static frontend, exposed via Cloudflare Tunnel.

## Standard Stack

The established deployment stack for Iyeska HQ:

### Core
| Component | Version | Purpose | Why Standard |
|-----------|---------|---------|--------------|
| PM2 | 5.x | Process manager | Already running wowasi_ya, n8n on server |
| Cloudflare Tunnel | latest | Public ingress | All *.iyeska.net domains use this |
| FastAPI StaticFiles | 0.115+ | Frontend serving | Consolidates deployment to single process |
| Python | 3.13 | Runtime | Iyeska standard (MacPorts `/opt/local/bin/python3.13`) |

### Supporting
| Component | Purpose | When to Use |
|-----------|---------|-------------|
| uvicorn | ASGI server | Always - run FastAPI in production |
| systemd | Service manager | Optional - PM2 handles restart/startup |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| PM2 | systemd | PM2 provides better monitoring, logs; systemd is native |
| StaticFiles | Nginx | Nginx is faster but adds complexity; StaticFiles sufficient for internal tool |
| Cloudflare Tunnel | Traefik + Let's Encrypt | Tunnel is already configured, simpler, no port exposure |

**Installation:**
```bash
# On Ubuntu server (already available)
pm2 --version  # Should be installed

# Python venv setup
/opt/local/bin/python3.13 -m venv .venv  # If on Mac
python3.11 -m venv .venv  # Ubuntu may use 3.11/3.12
source .venv/bin/activate
pip install -e ".[all]"
```

## Architecture Patterns

### Recommended Deployment Structure

```
/home/guthdx/projects/cosmograph/
├── .venv/                    # Python virtual environment
├── src/cosmograph/
│   └── api/main.py          # FastAPI app (serves static + API)
├── frontend/
│   └── dist/                # Built Vite output
├── templates/               # Jinja2 templates
├── ecosystem.config.js      # PM2 configuration
└── .env                     # Environment variables (if needed)
```

### Pattern 1: Single-Process Deployment

**What:** FastAPI serves both API endpoints and static frontend files
**When to use:** Internal tools, moderate traffic, simplified deployment
**Example:**
```python
# Source: FastAPI official docs + wowasi_ya pattern
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI()

# API routes first (more specific paths)
app.include_router(health.router)
app.include_router(extract.router)
app.include_router(graph.router)

# Static files mount (for assets)
frontend_dist = os.path.join(os.path.dirname(__file__), "../../frontend/dist")
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=f"{frontend_dist}/assets"), name="assets")

    @app.get("/", include_in_schema=False)
    async def serve_frontend():
        return FileResponse(f"{frontend_dist}/index.html")

    # Catch-all for SPA routing
    @app.get("/{path:path}", include_in_schema=False)
    async def serve_spa(path: str):
        file_path = f"{frontend_dist}/{path}"
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(f"{frontend_dist}/index.html")
```

### Pattern 2: PM2 Ecosystem Configuration

**What:** PM2 config file for managing the FastAPI process
**When to use:** Always for PM2-managed deployments
**Example:**
```javascript
// Source: wowasi_ya ecosystem.config.js (Iyeska standard)
module.exports = {
  apps: [{
    name: 'cosmograph',
    script: '.venv/bin/python',
    args: '-m uvicorn cosmograph.api.main:app --host 0.0.0.0 --port 8003',
    cwd: '/home/guthdx/projects/cosmograph',
    env: {
      ENVIRONMENT: 'production'
    },
    watch: false,
    instances: 1,
    autorestart: true,
    max_memory_restart: '1G'
  }]
}
```

### Pattern 3: Cloudflare Tunnel Ingress

**What:** Adding cosmograph.iyeska.net to Cloudflare Tunnel config
**When to use:** All public *.iyeska.net domains
**Example:**
```yaml
# Source: Ubuntu server ~/.cloudflared/config.yml
# Add this entry to existing ingress rules
ingress:
  # ... existing entries ...
  - hostname: cosmograph.iyeska.net
    service: http://localhost:8003
  # catch-all must be last
  - service: http_status:404
```

### Anti-Patterns to Avoid

- **Separate nginx/reverse proxy:** Cloudflare Tunnel already handles TLS termination and routing. Adding nginx would be redundant.
- **Gunicorn workers:** For internal tool with light load, single uvicorn process is sufficient. Workers add complexity.
- **Docker deployment:** Project uses PM2 pattern like wowasi_ya. Docker would be inconsistent with existing infrastructure.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Process management | Custom scripts | PM2 | Handles restart, logs, startup on boot |
| TLS certificates | Let's Encrypt + Traefik | Cloudflare Tunnel | Already configured, automatic cert management |
| Static file serving | nginx | FastAPI StaticFiles | Simpler, single process, sufficient for internal use |
| DNS management | Manual A records | Cloudflare Tunnel CNAME | Dynamic IP, no port exposure needed |
| Log rotation | Custom logrotate | PM2 logs | Built-in rotation, easily accessible |

**Key insight:** The Iyeska server already has proven patterns. Follow wowasi_ya deployment model exactly.

## Common Pitfalls

### Pitfall 1: Port Conflicts

**What goes wrong:** Cosmograph tries to use a port already in use (8001, 8002, etc.)
**Why it happens:** Multiple services on same server without port coordination
**How to avoid:** Use port 8003 (next available per PORT_REGISTRY.md)
**Warning signs:** "Address already in use" error, service won't start

### Pitfall 2: CORS Configuration Missing Production Origin

**What goes wrong:** Frontend can't reach API in production
**Why it happens:** CORS only allows localhost origins, not cosmograph.iyeska.net
**How to avoid:** Add `https://cosmograph.iyeska.net` to CORS allowed_origins
**Warning signs:** Browser console shows CORS errors, API calls fail

### Pitfall 3: Static Files Path Issues

**What goes wrong:** Frontend returns 404, assets missing
**Why it happens:** Relative paths don't work when deployed to different directory structure
**How to avoid:** Use absolute paths or calculate paths relative to module location
**Warning signs:** index.html loads but blank page, JS/CSS 404s in network tab

### Pitfall 4: Vite Base Path Not Set

**What goes wrong:** Assets load from wrong URLs in production
**Why it happens:** Vite defaults to absolute `/` paths
**How to avoid:** Set `base: './'` in vite.config.ts for relative paths
**Warning signs:** /assets/index.js returns 404, works in dev but not prod

### Pitfall 5: Cloudflare Tunnel Config YAML Errors

**What goes wrong:** Tunnel fails to start or routes incorrectly
**Why it happens:** YAML indentation or format errors in config.yml
**How to avoid:** Validate YAML, ensure hostname and service on same entry
**Warning signs:** `sudo journalctl -u cloudflared` shows config parse errors

### Pitfall 6: PM2 Environment Variables Not Loaded

**What goes wrong:** App starts but missing env vars (ANTHROPIC_API_KEY, etc.)
**Why it happens:** PM2 doesn't source .env files automatically
**How to avoid:** Use `pm2 restart cosmograph --update-env` after .env changes, or set env in ecosystem.config.js
**Warning signs:** LLM extraction fails, API key errors

## Code Examples

Verified patterns from Iyeska deployments:

### PM2 Ecosystem File
```javascript
// Source: wowasi_ya/ecosystem.config.js (verified working)
module.exports = {
  apps: [{
    name: 'cosmograph',
    script: '.venv/bin/python',
    args: '-m uvicorn cosmograph.api.main:app --host 0.0.0.0 --port 8003',
    cwd: '/home/guthdx/projects/cosmograph',
    env: {
      ENVIRONMENT: 'production',
      ANTHROPIC_API_KEY: 'set-via-dotenv-or-here'
    },
    watch: false,
    instances: 1,
    autorestart: true,
    max_memory_restart: '1G'
  }]
}
```

### CORS with Production Origin
```python
# Source: Current cosmograph/api/main.py (needs update)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://cosmograph.localhost",
        "https://cosmograph.iyeska.net",  # ADD THIS
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Vite Production Build Config
```typescript
// Source: Vite official docs + best practices
export default defineConfig({
  plugins: [react()],
  base: './',  // Relative paths for production
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
  },
});
```

### Cloudflare Tunnel Config Entry
```yaml
# Source: Ubuntu server ~/.cloudflared/config.yml pattern
tunnel: 1e02b2ec-7f02-4cf5-962f-0db3558e270c
credentials-file: /home/guthdx/.cloudflared/1e02b2ec-7f02-4cf5-962f-0db3558e270c.json

ingress:
  - hostname: n8n.iyeska.net
    service: http://localhost:5678
  - hostname: wowasi.iyeska.net
    service: http://localhost:8002
  - hostname: cosmograph.iyeska.net
    service: http://localhost:8003
  # catch-all must be last
  - service: http_status:404
```

### Deploy Script
```bash
#!/bin/bash
# Source: wowasi_ya/deploy.sh pattern (verified working)
set -e

cd /home/guthdx/projects/cosmograph

# Pull latest code
git pull origin main

# Update dependencies
source .venv/bin/activate
pip install -e ".[all]"

# Build frontend
cd frontend
npm ci
npm run build
cd ..

# Restart PM2 process
pm2 restart cosmograph --update-env

echo "Deployment complete. Check: pm2 logs cosmograph"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| nginx + gunicorn | Cloudflare Tunnel + uvicorn | 2024+ | Simpler TLS, no port exposure |
| Separate frontend server | FastAPI StaticFiles | 2024 | Single process deployment |
| Docker Compose | PM2 direct | Iyeska standard | Consistent with wowasi_ya |

**Deprecated/outdated:**
- Traefik for production: Use Cloudflare Tunnel instead for *.iyeska.net (Traefik is for local dev only)
- Separate frontend deployment: Consolidate with FastAPI for internal tools

## Open Questions

Things resolved during research:

1. **Port allocation for cosmograph**
   - Resolved: Use port 8003 (next available after wowasi_ya:8002)
   - Per PORT_REGISTRY.md allocation protocol

2. **DNS setup method**
   - Resolved: Cloudflare Tunnel (CNAME auto-created), not manual A record
   - Existing tunnel already handles *.iyeska.net routing

3. **Frontend serving strategy**
   - Resolved: FastAPI StaticFiles (matches wowasi_ya portal pattern)
   - Single process, no nginx needed

## Sources

### Primary (HIGH confidence)
- wowasi_ya/ecosystem.config.js - Verified PM2 config on same server
- wowasi_ya/CLAUDE.md - Deployment documentation (lines 319-340)
- ubuntu_server_docs/CLAUDE.md - Server infrastructure documentation
- PORT_REGISTRY.md - Port allocation (port 8003 available)
- Existing cosmograph/traefik/dynamic/cosmograph.yml - Dev Traefik config

### Secondary (MEDIUM confidence)
- [FastAPI Static Files](https://fastapi.tiangolo.com/tutorial/static-files/) - Official documentation
- [PM2 Quick Start](https://pm2.keymetrics.io/docs/usage/quick-start/) - Official docs
- [Travis Luong - FastAPI PM2 Nginx](https://www.travisluong.com/how-to-deploy-fastapi-with-nginx-and-pm2/) - Deployment guide

### Tertiary (LOW confidence)
- WebSearch results for Cloudflare Tunnel DNS Challenge - Verified against existing config

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Verified against existing wowasi_ya deployment
- Architecture: HIGH - Matches proven Iyeska patterns exactly
- Pitfalls: HIGH - Documented from real deployment experience

**Research date:** 2026-01-22
**Valid until:** 2026-03-22 (60 days - stable infrastructure patterns)

---

## Deployment Checklist Summary

For planner reference, the deployment tasks are:

1. **PM2 Configuration**
   - Create ecosystem.config.js (use wowasi_ya as template)
   - Port: 8003

2. **Frontend Build**
   - Update vite.config.ts with `base: './'`
   - Run `npm run build`
   - Modify FastAPI to serve static files

3. **CORS Update**
   - Add `https://cosmograph.iyeska.net` to allowed origins

4. **Cloudflare Tunnel**
   - Add ingress entry to `~/.cloudflared/config.yml`
   - Restart cloudflared service

5. **DNS**
   - Cloudflare Tunnel auto-creates CNAME (no manual DNS needed)

6. **Deploy**
   - Create deploy.sh script
   - Clone to `/home/guthdx/projects/cosmograph`
   - Start with PM2

7. **Validation**
   - Health check: `curl https://cosmograph.iyeska.net/health`
   - Frontend loads: browser test
   - Process real document
