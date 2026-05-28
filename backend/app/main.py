"""
Agitator Rye — FastAPI Application Entry Point.

Configures middleware, routes, startup events, and health check.
"""

import logging
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.database import create_tables
from app.data.synthetic_data import seed_database
from app.api.routes import chat, dashboard, analytics, pipeline

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("agitator_rye")
settings = get_settings()


# ── Lifespan (startup + shutdown) ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=== Agitator Rye starting up ===")
    try:
        create_tables()
        seed_database()
        logger.info("Database ready.")
    except Exception as e:
        logger.error("Startup error: %s", e)
    yield
    logger.info("=== Agitator Rye shutting down ===")


# ── FastAPI App ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Agitator Rye",
    description=(
        "Enterprise Analytics Intelligence Platform — "
        "Powered by LangChain + Sarvam AI"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Middleware ─────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(chat.router)
app.include_router(dashboard.router)
app.include_router(analytics.router)
app.include_router(pipeline.router)


# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
def health_check():
    """Platform health check endpoint."""
    from app.core.database import SessionLocal, Customer, SalesTransaction, DailyMetric
    db = SessionLocal()
    try:
        record_counts = {
            "customers": db.query(Customer).count(),
            "sales_transactions": db.query(SalesTransaction).count(),
            "daily_metrics": db.query(DailyMetric).count(),
        }
        db_ok = True
    except Exception:
        record_counts = {}
        db_ok = False
    finally:
        db.close()

    return {
        "status": "healthy",
        "version": "1.0.0",
        "platform": "Agitator Rye",
        "db_connected": db_ok,
        "record_counts": record_counts,
        "llm_provider": "Sarvam AI",
        "model": settings.sarvam_model,
    }


@app.get("/", tags=["System"])
def root():
    return {
        "message": "Agitator Rye Analytics Intelligence Platform",
        "docs": "/docs",
        "health": "/health",
        "version": "1.0.0",
    }
