# factsorlie — Claude notes

## Stack

- Flask app on port 5000, fronted by Apache (80/443) with Let's Encrypt TLS
- Redis for rate limiting and hit counter
- All three run via `docker compose` from this directory

## Live-mounted paths (no rebuild on edit)

The flask container mounts source directly from the host:

```
/home/ubuntu/factsorlie → /app    (rw)
/home/ubuntu/postWolf   → /postWolf (ro)
```

Consequences:

- **Template / HTML edits** (`templates/*.html`) → live on next request
- **CSS / static edits** (`static/*`) → live on next request (hard-refresh browser)
- **`app.py` or other Python edits** → `docker compose restart flask` (gunicorn doesn't auto-reload)
- **`requirements.txt` changes** → `docker compose up -d --build flask` (venv is baked into the image at `/opt/venv`)
- **postWolf README edits** → live immediately; the homepage reads `/postWolf/README.md` on every hit

## Homepage content

The `/` route (in `app.py::index`) reads `/postWolf/README.md` and renders
it as markdown into `templates/index.html`. To change the homepage body,
edit `~/postWolf/README-new.md` (which README.md symlinks to).

## Apache routes

- `/` → proxies to flask:5000
- `/wolfGuard/…` → serves Doxygen HTML from `/home/ubuntu/factsorlie/wolfGuard`
- `/.well-known/…` → Let's Encrypt ACME challenges

## Docker image layout

- Python venv at `/opt/venv` (baked in, survives the bind mount)
- `WORKDIR /app` — overridden at runtime by the host mount
- No `COPY . .` in the Dockerfile — the image is intentionally tiny;
  source comes from the mount

## Common commands

```bash
docker compose restart flask          # pick up app.py / Python changes
docker compose up -d --build flask    # rebuild (only needed for requirements.txt)
docker compose restart redis          # restart Redis
docker compose logs -f flask          # tail Flask logs
docker exec flask-app ls /app         # verify mount
```

## Navigation

The top nav is in `templates/base.html`. Routes like `/submit` and
`/wolfguard` still exist as Flask endpoints even when their nav links
are removed — deliberate choice (unlisted but reachable by URL).
