from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import engine, Base
from app.config import settings
from app.routers import auth, metrics, yaml_config

ALLOWED_ORIGINS = [
    settings.app_base_url,
    "http://localhost:5173",
    "http://localhost:8000",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="Tracking Success",
    description="Personal metrics tracker",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(metrics.router)
app.include_router(yaml_config.router)


@app.get("/health")
async def health():
    return {"status": "ok"}