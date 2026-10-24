# Deploying BrandCheck (one public link: UI + API together)

The `Dockerfile` builds the React app, then FastAPI serves both the UI and the API from the same address, so no CORS or second hosting is needed.

## Render (free) — about 10 minutes
1. Push this repository to GitHub (public).
2. Go to https://render.com -> sign in with GitHub -> **New +** -> **Blueprint** (or **Web Service**) -> pick this repo.
   - Blueprint: Render reads `render.yaml` automatically.
   - Web Service: Runtime = **Docker**, Plan = **Free**, Health check path = `/health`, add env var `SECRET_KEY` = any long random string.
3. Click **Deploy**. When the build finishes, open the `https://<name>.onrender.com` link.

## Things to know
- Default database is SQLite inside the container. On free hosting the container sleeps after ~15 minutes idle and starts fresh, so **drafts and uploads created by visitors can disappear; demo data is re-seeded automatically.** The first request after sleeping takes up to ~1 minute.
- For persistent data, set `DATABASE_URL` to a PostgreSQL URL (the code supports it; not tested by us on the hosted demo).
- Optional contextual AI is **off** unless `OPENAI_API_KEY` is set. Never commit `.env`.
- Demo accounts are seeded and passwords are demo-only. Change `SECRET_KEY` and remove demo users before any real use.
