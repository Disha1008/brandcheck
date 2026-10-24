from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine, SessionLocal
import models  # noqa: F401  (registers tables)
from seed import seed
from routes import auth_routes, guidelines, drafts, insights


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed(db)
    yield


app = FastAPI(title="BrandCheck API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)
app.include_router(auth_routes.router)
app.include_router(guidelines.router)
app.include_router(drafts.router)
app.include_router(insights.router)


@app.get("/")
def health():
    return {"status": "ok", "app": "BrandCheck"}
