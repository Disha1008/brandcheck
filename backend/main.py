from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine, SessionLocal
import models  # noqa: F401  (registers tables)
import os
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from seed import seed
from routes import auth_routes, guidelines, drafts, insights, assets


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed(db)
    yield


app = FastAPI(title="BrandCheck API", version="1.0.0", description="Explainable, human-controlled brand content governance", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]
    + [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)
app.include_router(auth_routes.router)
app.include_router(guidelines.router)
app.include_router(drafts.router)
app.include_router(insights.router)
app.include_router(assets.router)


@app.get("/health")
def health():
    return {"status": "ok", "app": "BrandCheck", "contextual_ai_enabled": bool(os.getenv("OPENAI_API_KEY", "").strip()), "database": "configured"}


# In production the built React app (frontend/dist) is served by this same server,
# so one public link serves both the UI and the API. Locally (no dist folder) "/" is the health check.
DIST = Path(__file__).resolve().parents[1] / "frontend" / "dist"
if DIST.is_dir():
    app.mount("/", StaticFiles(directory=DIST, html=True), name="frontend")
else:
    @app.get("/")
    def root():
        return health()
