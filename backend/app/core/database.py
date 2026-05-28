"""SQLAlchemy database setup — engine, session, and table definitions."""

import logging
from contextlib import contextmanager
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Float,
    Integer,
    Date,
    DateTime,
    Text,
    Boolean,
    event,
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Engine ──────────────────────────────────────────────────────────────────
connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    echo=False,
    pool_pre_ping=True,
)

# Enable WAL mode for SQLite (better concurrency)
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    if settings.database_url.startswith("sqlite"):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ── ORM Models ───────────────────────────────────────────────────────────────

class Customer(Base):
    __tablename__ = "customers"
    customer_id = Column(String(36), primary_key=True)
    name = Column(String(120))
    email = Column(String(120))
    region = Column(String(50))
    country = Column(String(80))
    segment = Column(String(50))
    acquisition_channel = Column(String(50))
    clv = Column(Float)
    age_group = Column(String(20))
    signup_date = Column(Date)
    is_active = Column(Boolean, default=True)


class Product(Base):
    __tablename__ = "products"
    product_id = Column(String(36), primary_key=True)
    name = Column(String(150))
    category = Column(String(80))
    subcategory = Column(String(80))
    brand = Column(String(80))
    price = Column(Float)
    cost = Column(Float)
    margin_pct = Column(Float)
    is_active = Column(Boolean, default=True)


class SalesTransaction(Base):
    __tablename__ = "sales_transactions"
    transaction_id = Column(String(36), primary_key=True)
    date = Column(Date, index=True)
    customer_id = Column(String(36), index=True)
    product_id = Column(String(36), index=True)
    amount = Column(Float)
    quantity = Column(Integer)
    region = Column(String(50), index=True)
    channel = Column(String(50), index=True)
    category = Column(String(80), index=True)
    discount_pct = Column(Float)
    profit = Column(Float)
    country = Column(String(80))
    sales_rep = Column(String(80))


class DailyMetric(Base):
    __tablename__ = "daily_metrics"
    date = Column(Date, primary_key=True)
    revenue = Column(Float)
    orders = Column(Integer)
    sessions = Column(Integer)
    conversion_rate = Column(Float)
    nps = Column(Float)
    new_customers = Column(Integer)
    avg_order_value = Column(Float)
    churn_rate = Column(Float)
    support_tickets = Column(Integer)


class FinancialData(Base):
    __tablename__ = "financial_data"
    month = Column(String(7), primary_key=True)   # YYYY-MM
    revenue = Column(Float)
    cogs = Column(Float)
    gross_profit = Column(Float)
    gross_margin = Column(Float)
    opex = Column(Float)
    ebitda = Column(Float)
    net_income = Column(Float)
    net_margin = Column(Float)
    cash_flow = Column(Float)
    headcount = Column(Integer)


class WebAnalytic(Base):
    __tablename__ = "web_analytics"
    date = Column(Date, primary_key=True)
    sessions = Column(Integer)
    pageviews = Column(Integer)
    unique_visitors = Column(Integer)
    bounce_rate = Column(Float)
    avg_session_duration = Column(Float)
    goal_completions = Column(Integer)
    conversion_rate = Column(Float)
    organic_sessions = Column(Integer)
    paid_sessions = Column(Integer)


class AnomalyEvent(Base):
    __tablename__ = "anomaly_events"
    event_id = Column(String(36), primary_key=True)
    metric = Column(String(80), index=True)
    detected_at = Column(DateTime, index=True)
    actual_value = Column(Float)
    expected_value = Column(Float)
    z_score = Column(Float)
    severity = Column(String(20))
    status = Column(String(20), default="open")
    dimension = Column(String(80))
    dimension_value = Column(String(80))
    notes = Column(Text)


class PipelineLog(Base):
    __tablename__ = "pipeline_logs"
    run_id = Column(String(36), primary_key=True)
    pipeline_name = Column(String(80))
    stage = Column(String(80))
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    status = Column(String(20))
    rows_in = Column(Integer)
    rows_out = Column(Integer)
    issues_found = Column(Integer)
    quality_score = Column(Float)
    notes = Column(Text)


# ── Helpers ──────────────────────────────────────────────────────────────────

def create_tables():
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified.")


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
