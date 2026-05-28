"""
Synthetic data generator for Agitator Rye.

Generates a realistic, large-scale dataset across 8 tables:
  • 15,000 customers
  • 500 products
  • 150,000 sales transactions
  • 1,825 days of daily metrics  (5 years)
  • 60 months of financial data
  • 1,825 days of web analytics
  • ~200 anomaly events
  • Pipeline log seeds
"""

import uuid
import random
import logging
from datetime import date, datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
from faker import Faker
from sqlalchemy.orm import Session

from app.core.database import (
    SessionLocal,
    create_tables,
    Customer,
    Product,
    SalesTransaction,
    DailyMetric,
    FinancialData,
    WebAnalytic,
    AnomalyEvent,
    PipelineLog,
)

logger = logging.getLogger(__name__)
fake = Faker()
rng = np.random.default_rng(42)
random.seed(42)

# ── Constants ────────────────────────────────────────────────────────────────

REGIONS = ["North America", "Europe", "Asia Pacific", "Latin America", "Middle East & Africa"]
COUNTRIES_BY_REGION = {
    "North America": ["United States", "Canada", "Mexico"],
    "Europe": ["United Kingdom", "Germany", "France", "Netherlands", "Sweden"],
    "Asia Pacific": ["India", "Japan", "Australia", "Singapore", "South Korea"],
    "Latin America": ["Brazil", "Argentina", "Colombia", "Chile"],
    "Middle East & Africa": ["UAE", "Saudi Arabia", "South Africa", "Nigeria"],
}
CHANNELS = ["Online", "Retail", "Enterprise", "Partner", "Direct Sales"]
SEGMENTS = ["Enterprise", "Mid-Market", "SMB", "Consumer"]
ACQ_CHANNELS = ["Organic Search", "Paid Search", "Social Media", "Referral", "Email", "Direct", "Partner"]
AGE_GROUPS = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]

CATEGORIES = {
    "Electronics": ["Laptops", "Smartphones", "Tablets", "Accessories", "Wearables"],
    "Software": ["Productivity", "Security", "Analytics", "Communication", "Development"],
    "Cloud Services": ["Compute", "Storage", "Database", "AI/ML", "Networking"],
    "Hardware": ["Servers", "Networking Gear", "Peripherals", "Printers", "Cameras"],
    "Professional Services": ["Consulting", "Training", "Support", "Implementation", "Audit"],
}

BRANDS = [
    "TechCore", "NexGen", "Apex Solutions", "DataFlow", "CloudBridge",
    "Prism Tech", "Velocity Systems", "Quantum Edge", "Pinnacle AI", "HorizonX"
]

SALES_REPS = [
    "Alex Chen", "Jordan Smith", "Maria Garcia", "David Kim", "Sarah Johnson",
    "Mohammed Al-Rashid", "Emma Williams", "Carlos Mendez", "Priya Patel", "James O'Brien",
    "Yuki Tanaka", "Anna Kowalski", "Raj Sharma", "Lisa Thompson", "Mike Davis",
    "Sophie Martin", "Diego Rodriguez", "Amy Zhang", "Tom Wilson", "Fatima Hassan"
]

START_DATE = date(2021, 1, 1)
END_DATE = date(2025, 12, 31)
N_DAYS = (END_DATE - START_DATE).days + 1


# ── Helper Functions ──────────────────────────────────────────────────────────

def _uid() -> str:
    return str(uuid.uuid4())


def _date_range(start: date, n_days: int) -> list[date]:
    return [start + timedelta(days=i) for i in range(n_days)]


def _add_trend(base: float, day_idx: int, n_days: int, growth: float = 0.15) -> float:
    """Add linear growth trend."""
    return base * (1 + growth * day_idx / n_days)


def _add_seasonality(value: float, day_of_year: int) -> float:
    """Add yearly seasonality (Q4 peak, Q1 trough)."""
    seasonal = 1 + 0.25 * np.sin(2 * np.pi * (day_of_year - 90) / 365)
    return value * seasonal


def _add_weekly(value: float, weekday: int) -> float:
    """Weekday boost Mon-Fri, weekend dip."""
    mult = [0.75, 1.05, 1.10, 1.12, 1.15, 0.80, 0.70][weekday]
    return value * mult


def _add_noise(value: float, noise_pct: float = 0.05) -> float:
    return value * (1 + rng.normal(0, noise_pct))


# ── Customer Generation ───────────────────────────────────────────────────────

def _generate_customers(n: int = 15_000) -> list[dict]:
    logger.info("Generating %d customers...", n)
    customers = []
    for _ in range(n):
        region = random.choice(REGIONS)
        country = random.choice(COUNTRIES_BY_REGION[region])
        segment = random.choices(
            SEGMENTS, weights=[0.15, 0.25, 0.40, 0.20]
        )[0]
        clv_base = {"Enterprise": 85_000, "Mid-Market": 25_000, "SMB": 8_000, "Consumer": 1_500}[segment]
        clv = max(100.0, rng.normal(clv_base, clv_base * 0.3))
        customers.append({
            "customer_id": _uid(),
            "name": fake.company() if segment != "Consumer" else fake.name(),
            "email": fake.email(),
            "region": region,
            "country": country,
            "segment": segment,
            "acquisition_channel": random.choice(ACQ_CHANNELS),
            "clv": round(clv, 2),
            "age_group": random.choice(AGE_GROUPS),
            "signup_date": fake.date_between(START_DATE, END_DATE - timedelta(days=30)),
            "is_active": random.random() > 0.08,
        })
    return customers


# ── Product Generation ────────────────────────────────────────────────────────

def _generate_products(n: int = 500) -> list[dict]:
    logger.info("Generating %d products...", n)
    products = []
    for _ in range(n):
        category = random.choice(list(CATEGORIES.keys()))
        subcategory = random.choice(CATEGORIES[category])
        price_base = {
            "Electronics": 850, "Software": 3500, "Cloud Services": 2000,
            "Hardware": 1500, "Professional Services": 5000
        }[category]
        price = round(max(10.0, rng.lognormal(np.log(price_base), 0.5)), 2)
        margin = random.uniform(0.20, 0.75)
        cost = round(price * (1 - margin), 2)
        products.append({
            "product_id": _uid(),
            "name": f"{random.choice(BRANDS)} {subcategory} {fake.bothify('??-###')}",
            "category": category,
            "subcategory": subcategory,
            "brand": random.choice(BRANDS),
            "price": price,
            "cost": cost,
            "margin_pct": round(margin * 100, 2),
            "is_active": random.random() > 0.05,
        })
    return products


# ── Sales Transactions ────────────────────────────────────────────────────────

def _generate_transactions(
    customer_ids: list[str],
    product_data: list[dict],
    n: int = 150_000,
) -> list[dict]:
    logger.info("Generating %d sales transactions...", n)
    all_dates = _date_range(START_DATE, N_DAYS)
    # Weight recent dates higher
    date_weights = np.linspace(0.5, 1.5, len(all_dates))
    date_weights /= date_weights.sum()

    transactions = []
    for _ in range(n):
        tx_date = np.random.choice(all_dates, p=date_weights)
        product = random.choice(product_data)
        customer_id = random.choice(customer_ids)
        quantity = max(1, int(rng.lognormal(0.5, 0.7)))
        discount = round(random.choices([0, 0.05, 0.10, 0.15, 0.20, 0.25], weights=[40,20,15,12,8,5])[0], 2)
        unit_price = product["price"] * (1 - discount)
        amount = round(unit_price * quantity, 2)
        profit = round((product["price"] - product["cost"]) * quantity * (1 - discount), 2)
        region = random.choices(REGIONS, weights=[35, 30, 20, 10, 5])[0]

        transactions.append({
            "transaction_id": _uid(),
            "date": tx_date,
            "customer_id": customer_id,
            "product_id": product["product_id"],
            "amount": amount,
            "quantity": quantity,
            "region": region,
            "channel": random.choices(CHANNELS, weights=[30, 25, 20, 15, 10])[0],
            "category": product["category"],
            "discount_pct": discount * 100,
            "profit": profit,
            "country": random.choice(COUNTRIES_BY_REGION[region]),
            "sales_rep": random.choice(SALES_REPS),
        })
    return transactions


# ── Daily Metrics ─────────────────────────────────────────────────────────────

def _generate_daily_metrics() -> list[dict]:
    logger.info("Generating daily metrics for %d days...", N_DAYS)
    dates = _date_range(START_DATE, N_DAYS)
    metrics = []
    base_revenue = 250_000
    base_orders = 1_200
    base_sessions = 45_000

    for i, d in enumerate(dates):
        day_of_year = d.timetuple().tm_yday
        weekday = d.weekday()

        revenue = _add_noise(
            _add_weekly(_add_seasonality(_add_trend(base_revenue, i, N_DAYS, 0.18), day_of_year), weekday),
            0.08,
        )
        # Inject deliberate anomalies for RCA demo
        if d == date(2023, 11, 24):   # Black Friday spike
            revenue *= 4.2
        if d == date(2024, 3, 15):    # Simulated outage
            revenue *= 0.35

        orders = max(1, int(_add_noise(_add_weekly(_add_trend(base_orders, i, N_DAYS, 0.15), weekday), 0.10)))
        sessions = max(1, int(_add_noise(_add_weekly(_add_seasonality(_add_trend(base_sessions, i, N_DAYS, 0.20), day_of_year), weekday), 0.07)))
        conv_rate = round(min(0.08, max(0.01, _add_noise(orders / sessions, 0.05))), 4)
        aov = round(revenue / max(orders, 1), 2)

        metrics.append({
            "date": d,
            "revenue": round(revenue, 2),
            "orders": orders,
            "sessions": sessions,
            "conversion_rate": conv_rate,
            "nps": round(min(100, max(-100, _add_noise(45, 0.15))), 1),
            "new_customers": max(0, int(_add_noise(_add_trend(120, i, N_DAYS, 0.10), 0.15))),
            "avg_order_value": aov,
            "churn_rate": round(max(0, _add_noise(0.018, 0.20)), 4),
            "support_tickets": max(0, int(_add_noise(_add_trend(95, i, N_DAYS, -0.05), 0.15))),
        })
    return metrics


# ── Financial Data ────────────────────────────────────────────────────────────

def _generate_financial_data() -> list[dict]:
    logger.info("Generating 60 months of financial data...")
    records = []
    base_rev = 7_500_000
    for m in range(60):
        month_date = START_DATE + timedelta(days=m * 30)
        month_str = month_date.strftime("%Y-%m")
        revenue = round(_add_noise(_add_trend(base_rev, m, 60, 0.22), 0.05), 2)
        cogs_pct = random.uniform(0.38, 0.52)
        cogs = round(revenue * cogs_pct, 2)
        gross_profit = round(revenue - cogs, 2)
        gross_margin = round((gross_profit / revenue) * 100, 2) if revenue else 0
        opex = round(revenue * random.uniform(0.28, 0.38), 2)
        ebitda = round(gross_profit - opex, 2)
        net_income = round(ebitda * random.uniform(0.60, 0.80), 2)
        net_margin = round((net_income / revenue) * 100, 2) if revenue else 0
        cash_flow = round(net_income + _add_noise(200_000, 0.30), 2)
        headcount = int(_add_trend(120, m, 60, 0.50) + rng.normal(0, 3))

        records.append({
            "month": month_str,
            "revenue": revenue,
            "cogs": cogs,
            "gross_profit": gross_profit,
            "gross_margin": gross_margin,
            "opex": opex,
            "ebitda": ebitda,
            "net_income": net_income,
            "net_margin": net_margin,
            "cash_flow": cash_flow,
            "headcount": max(100, headcount),
        })
    return records


# ── Web Analytics ─────────────────────────────────────────────────────────────

def _generate_web_analytics() -> list[dict]:
    logger.info("Generating web analytics for %d days...", N_DAYS)
    dates = _date_range(START_DATE, N_DAYS)
    records = []
    base_sessions = 38_000

    for i, d in enumerate(dates):
        day_of_year = d.timetuple().tm_yday
        weekday = d.weekday()
        sessions = max(100, int(_add_noise(
            _add_weekly(_add_seasonality(_add_trend(base_sessions, i, N_DAYS, 0.25), day_of_year), weekday),
            0.08,
        )))
        pageviews = max(sessions, int(sessions * _add_noise(2.8, 0.10)))
        unique_visitors = int(sessions * _add_noise(0.72, 0.05))
        bounce_rate = round(max(0.20, min(0.85, _add_noise(0.48, 0.08))), 3)
        avg_duration = round(max(30, _add_noise(185, 0.12)), 1)
        goals = max(0, int(sessions * _add_noise(0.032, 0.15)))
        conv_rate = round(goals / sessions, 4) if sessions else 0
        organic = int(sessions * random.uniform(0.35, 0.50))
        paid = int(sessions * random.uniform(0.15, 0.25))

        records.append({
            "date": d,
            "sessions": sessions,
            "pageviews": pageviews,
            "unique_visitors": unique_visitors,
            "bounce_rate": bounce_rate,
            "avg_session_duration": avg_duration,
            "goal_completions": goals,
            "conversion_rate": conv_rate,
            "organic_sessions": organic,
            "paid_sessions": paid,
        })
    return records


# ── Anomaly Events ────────────────────────────────────────────────────────────

def _generate_anomaly_events() -> list[dict]:
    logger.info("Generating anomaly events...")
    events = [
        {
            "event_id": _uid(),
            "metric": "revenue",
            "detected_at": datetime(2023, 11, 24, 8, 0),
            "actual_value": 1_050_000,
            "expected_value": 250_000,
            "z_score": 8.4,
            "severity": "info",
            "status": "resolved",
            "dimension": "channel",
            "dimension_value": "Online",
            "notes": "Black Friday peak — expected spike",
        },
        {
            "event_id": _uid(),
            "metric": "revenue",
            "detected_at": datetime(2024, 3, 15, 14, 22),
            "actual_value": 87_500,
            "expected_value": 265_000,
            "z_score": -5.2,
            "severity": "critical",
            "status": "resolved",
            "dimension": "region",
            "dimension_value": "North America",
            "notes": "Payment gateway outage — 67% revenue drop",
        },
        {
            "event_id": _uid(),
            "metric": "conversion_rate",
            "detected_at": datetime(2024, 7, 10, 10, 0),
            "actual_value": 0.018,
            "expected_value": 0.042,
            "z_score": -3.8,
            "severity": "high",
            "status": "investigating",
            "dimension": "channel",
            "dimension_value": "Paid Search",
            "notes": "Conversion rate anomaly in Paid Search — possible landing page issue",
        },
        {
            "event_id": _uid(),
            "metric": "sessions",
            "detected_at": datetime(2025, 2, 14, 0, 0),
            "actual_value": 125_000,
            "expected_value": 42_000,
            "z_score": 6.1,
            "severity": "info",
            "status": "resolved",
            "dimension": "source",
            "dimension_value": "Organic Search",
            "notes": "Viral blog post drove 3x organic traffic",
        },
        {
            "event_id": _uid(),
            "metric": "churn_rate",
            "detected_at": datetime(2025, 5, 1, 9, 0),
            "actual_value": 0.048,
            "expected_value": 0.018,
            "z_score": 4.2,
            "severity": "high",
            "status": "open",
            "dimension": "segment",
            "dimension_value": "SMB",
            "notes": "SMB churn spike — requires immediate investigation",
        },
    ]
    return events


# ── Pipeline Logs ─────────────────────────────────────────────────────────────

def _generate_pipeline_logs() -> list[dict]:
    logger.info("Generating pipeline logs...")
    logs = []
    stages = ["ingest", "schema_check", "quality_check", "clean", "validate", "load"]
    for i in range(30):
        run_id = _uid()
        start = datetime(2025, 1, 1) + timedelta(days=i * 5, hours=2)
        for j, stage in enumerate(stages):
            rows_in = 150_000 - i * 100
            issues = max(0, int(rng.normal(45, 15))) if stage == "quality_check" else 0
            rows_out = rows_in - (issues if stage == "clean" else 0)
            score = max(60.0, min(100.0, 95 - issues * 0.05 + rng.normal(0, 1)))
            logs.append({
                "run_id": f"{run_id}-{j}",
                "pipeline_name": "sales_etl",
                "stage": stage,
                "started_at": start + timedelta(minutes=j * 3),
                "completed_at": start + timedelta(minutes=j * 3 + 2),
                "status": "success" if random.random() > 0.04 else "warning",
                "rows_in": rows_in,
                "rows_out": rows_out,
                "issues_found": issues,
                "quality_score": round(score, 2),
                "notes": f"Stage {stage} completed" + (" — anomalies flagged" if issues > 80 else ""),
            })
    return logs


# ── Main Seed Function ────────────────────────────────────────────────────────

def seed_database():
    """Create all tables and populate with synthetic data. Safe to re-run (skips if data exists)."""
    create_tables()

    db: Session = SessionLocal()
    try:
        # Check if already seeded
        existing = db.query(Customer).first()
        if existing:
            logger.info("Database already seeded — skipping.")
            return

        logger.info("=== Starting Agitator Rye database seed ===")

        # 1. Customers
        customers = _generate_customers(15_000)
        db.bulk_insert_mappings(Customer, customers)
        db.commit()
        logger.info("✓ Customers: %d", len(customers))

        # 2. Products
        products = _generate_products(500)
        db.bulk_insert_mappings(Product, products)
        db.commit()
        logger.info("✓ Products: %d", len(products))

        # 3. Sales Transactions
        customer_ids = [c["customer_id"] for c in customers]
        transactions = _generate_transactions(customer_ids, products, 150_000)
        # Bulk insert in batches for SQLite performance
        batch_size = 10_000
        for i in range(0, len(transactions), batch_size):
            db.bulk_insert_mappings(SalesTransaction, transactions[i:i + batch_size])
            db.commit()
            logger.info("  transactions batch %d/%d committed", i // batch_size + 1, len(transactions) // batch_size + 1)
        logger.info("✓ Sales Transactions: %d", len(transactions))

        # 4. Daily Metrics
        daily = _generate_daily_metrics()
        db.bulk_insert_mappings(DailyMetric, daily)
        db.commit()
        logger.info("✓ Daily Metrics: %d", len(daily))

        # 5. Financial Data
        financial = _generate_financial_data()
        db.bulk_insert_mappings(FinancialData, financial)
        db.commit()
        logger.info("✓ Financial Data: %d months", len(financial))

        # 6. Web Analytics
        web = _generate_web_analytics()
        db.bulk_insert_mappings(WebAnalytic, web)
        db.commit()
        logger.info("✓ Web Analytics: %d", len(web))

        # 7. Anomaly Events
        anomalies = _generate_anomaly_events()
        db.bulk_insert_mappings(AnomalyEvent, anomalies)
        db.commit()
        logger.info("✓ Anomaly Events: %d", len(anomalies))

        # 8. Pipeline Logs
        plogs = _generate_pipeline_logs()
        db.bulk_insert_mappings(PipelineLog, plogs)
        db.commit()
        logger.info("✓ Pipeline Logs: %d", len(plogs))

        logger.info("=== Database seed complete! ===")

    except Exception as e:
        db.rollback()
        logger.error("Seed failed: %s", e)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_database()
