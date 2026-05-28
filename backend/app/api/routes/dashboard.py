"""Dashboard API — KPIs, charts, anomalies, and pipeline health."""

import logging
from datetime import date, timedelta, datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import pandas as pd
import numpy as np

from app.core.database import (
    get_db,
    DailyMetric,
    SalesTransaction,
    AnomalyEvent,
    PipelineLog,
    FinancialData,
    WebAnalytic,
)
from app.models.schemas import (
    DashboardKPIs,
    KPICard,
    SalesTrendResponse,
    ChartSeries,
    TimeSeriesPoint,
    RevenueBreakdownResponse,
    BarDataPoint,
    AnomalyAlertResponse,
    PipelineHealthResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


def _latest_date(db: Session) -> date:
    """Return most recent date in DailyMetric table (fallback: yesterday)."""
    result = db.query(func.max(DailyMetric.date)).scalar()
    return result or date.today() - timedelta(days=1)


def _safe_mean(values: list) -> float:
    """np.mean that never returns NaN."""
    if not values:
        return 0.0
    m = float(np.mean(values))
    return 0.0 if (m != m) else m  # NaN check


def _format_currency(v: float) -> str:
    if v >= 1_000_000:
        return f"${v/1_000_000:.2f}M"
    if v >= 1_000:
        return f"${v/1_000:.1f}K"
    return f"${v:.2f}"


def _trend(delta: float) -> str:
    if delta > 0.5:
        return "up"
    if delta < -0.5:
        return "down"
    return "neutral"


@router.get("/kpis", response_model=DashboardKPIs)
def get_kpis(db: Session = Depends(get_db)):
    """Return KPI summary cards for the executive dashboard."""
    period_end = _latest_date(db)
    period_start = period_end - timedelta(days=29)
    prior_start = period_start - timedelta(days=30)
    prior_end = period_start - timedelta(days=1)

    def _sum(col, d_from, d_to):
        result = db.query(func.sum(col)).filter(
            DailyMetric.date >= d_from, DailyMetric.date <= d_to
        ).scalar()
        return float(result or 0)

    def _avg(col, d_from, d_to):
        result = db.query(func.avg(col)).filter(
            DailyMetric.date >= d_from, DailyMetric.date <= d_to
        ).scalar()
        return float(result or 0)

    rev_cur = _sum(DailyMetric.revenue, period_start, period_end)
    rev_prior = _sum(DailyMetric.revenue, prior_start, prior_end)
    rev_delta = ((rev_cur - rev_prior) / rev_prior * 100) if rev_prior else 0

    orders_cur = _sum(DailyMetric.orders, period_start, period_end)
    orders_prior = _sum(DailyMetric.orders, prior_start, prior_end)
    orders_delta = ((orders_cur - orders_prior) / orders_prior * 100) if orders_prior else 0

    conv_cur = _avg(DailyMetric.conversion_rate, period_start, period_end) * 100
    conv_prior = _avg(DailyMetric.conversion_rate, prior_start, prior_end) * 100
    conv_delta = conv_cur - conv_prior

    new_cust_cur = _sum(DailyMetric.new_customers, period_start, period_end)
    new_cust_prior = _sum(DailyMetric.new_customers, prior_start, prior_end)
    new_cust_delta = ((new_cust_cur - new_cust_prior) / new_cust_prior * 100) if new_cust_prior else 0

    nps_cur = _avg(DailyMetric.nps, period_start, period_end)
    nps_prior = _avg(DailyMetric.nps, prior_start, prior_end)
    nps_delta = nps_cur - nps_prior

    aov_cur = _avg(DailyMetric.avg_order_value, period_start, period_end)
    aov_prior = _avg(DailyMetric.avg_order_value, prior_start, prior_end)
    aov_delta = ((aov_cur - aov_prior) / aov_prior * 100) if aov_prior else 0

    kpis = [
        KPICard(
            title="Total Revenue",
            value=rev_cur,
            formatted_value=_format_currency(rev_cur),
            delta=round(rev_delta, 2),
            delta_label="vs prior 30d",
            trend=_trend(rev_delta),
            icon="dollar-sign",
        ),
        KPICard(
            title="Total Orders",
            value=orders_cur,
            formatted_value=f"{orders_cur:,.0f}",
            delta=round(orders_delta, 2),
            delta_label="vs prior 30d",
            trend=_trend(orders_delta),
            icon="shopping-cart",
        ),
        KPICard(
            title="Conversion Rate",
            value=conv_cur,
            formatted_value=f"{conv_cur:.2f}%",
            delta=round(conv_delta, 2),
            delta_label="pp vs prior 30d",
            trend=_trend(conv_delta),
            icon="target",
        ),
        KPICard(
            title="New Customers",
            value=new_cust_cur,
            formatted_value=f"{new_cust_cur:,.0f}",
            delta=round(new_cust_delta, 2),
            delta_label="vs prior 30d",
            trend=_trend(new_cust_delta),
            icon="users",
        ),
        KPICard(
            title="Net Promoter Score",
            value=nps_cur,
            formatted_value=f"{nps_cur:.1f}",
            delta=round(nps_delta, 2),
            delta_label="pts vs prior 30d",
            trend=_trend(nps_delta),
            icon="star",
        ),
        KPICard(
            title="Avg Order Value",
            value=aov_cur,
            formatted_value=_format_currency(aov_cur),
            delta=round(aov_delta, 2),
            delta_label="vs prior 30d",
            trend=_trend(aov_delta),
            icon="trending-up",
        ),
    ]

    return DashboardKPIs(kpis=kpis, last_updated=datetime.utcnow())


@router.get("/sales-trend")
def get_sales_trend(
    days: int = Query(default=90, ge=7, le=365),
    db: Session = Depends(get_db),
):
    """Return revenue + orders time-series for the last N days."""
    d_to = _latest_date(db)
    d_from = d_to - timedelta(days=days - 1)

    rows = (
        db.query(DailyMetric)
        .filter(DailyMetric.date >= d_from, DailyMetric.date <= d_to)
        .order_by(DailyMetric.date)
        .all()
    )

    revenue_series = [{"date": str(r.date), "value": r.revenue} for r in rows]
    orders_series = [{"date": str(r.date), "value": float(r.orders)} for r in rows]
    sessions_series = [{"date": str(r.date), "value": float(r.sessions)} for r in rows]

    return {
        "period": f"{d_from} to {d_to}",
        "series": [
            {"name": "Revenue", "data": revenue_series, "color": "#00D4FF"},
            {"name": "Orders", "data": orders_series, "color": "#7B3FE4"},
            {"name": "Sessions", "data": sessions_series, "color": "#00C896"},
        ],
    }


@router.get("/revenue-breakdown")
def get_revenue_breakdown(
    days: int = Query(default=30, ge=7, le=365),
    db: Session = Depends(get_db),
):
    """Revenue breakdown by region, channel, and category."""
    d_to = _latest_date(db)
    d_from = d_to - timedelta(days=days - 1)

    rows = (
        db.query(SalesTransaction)
        .filter(SalesTransaction.date >= d_from, SalesTransaction.date <= d_to)
        .all()
    )

    if not rows:
        return {"by_region": [], "by_channel": [], "by_category": []}

    df = pd.DataFrame([{
        "amount": r.amount,
        "region": r.region,
        "channel": r.channel,
        "category": r.category,
    } for r in rows])

    COLORS = ["#00D4FF", "#7B3FE4", "#00C896", "#FFB800", "#FF4757", "#FF6B35", "#4ECDC4"]

    def agg(col):
        g = df.groupby(col)["amount"].sum().sort_values(ascending=False)
        return [{"name": k, "value": round(v, 2), "color": COLORS[i % len(COLORS)]} for i, (k, v) in enumerate(g.items())]

    return {
        "by_region": agg("region"),
        "by_channel": agg("channel"),
        "by_category": agg("category"),
    }


@router.get("/anomalies")
def get_anomalies(
    status: str = Query(default="open"),
    db: Session = Depends(get_db),
):
    """Return current anomaly alerts."""
    query = db.query(AnomalyEvent)
    if status != "all":
        query = query.filter(AnomalyEvent.status == status)
    rows = query.order_by(desc(AnomalyEvent.detected_at)).limit(20).all()
    return [
        {
            "event_id": r.event_id,
            "metric": r.metric,
            "severity": r.severity,
            "actual_value": r.actual_value,
            "expected_value": r.expected_value,
            "z_score": r.z_score,
            "detected_at": r.detected_at.isoformat() if r.detected_at else None,
            "status": r.status,
            "dimension": r.dimension,
            "dimension_value": r.dimension_value,
            "notes": r.notes,
        }
        for r in rows
    ]


@router.get("/pipeline-health")
def get_pipeline_health(db: Session = Depends(get_db)):
    """Return data pipeline health summary."""
    rows = db.query(PipelineLog).order_by(desc(PipelineLog.started_at)).limit(200).all()
    if not rows:
        return {
            "overall_score": 0,
            "last_run": None,
            "total_runs": 0,
            "success_rate": 0,
            "stages": [],
        }

    success = sum(1 for r in rows if r.status == "success")
    scores = [r.quality_score for r in rows if r.quality_score]

    stage_stats: dict[str, list] = {}
    for r in rows:
        stage_stats.setdefault(r.stage, []).append(r)

    stages = [
        {
            "name": stage or "unknown",
            "avg_score": round(_safe_mean([s.quality_score for s in items if s.quality_score is not None]), 2),
            "success_rate": round(sum(1 for s in items if s.status == "success") / len(items) * 100, 2),
            "last_run": (
                max((s.started_at for s in items if s.started_at), default=None) or datetime.utcnow()
            ).isoformat(),
        }
        for stage, items in stage_stats.items()
    ]

    return {
        "overall_score": round(_safe_mean(scores), 2),
        "last_run": rows[0].started_at.isoformat() if rows[0].started_at else None,
        "total_runs": len(rows),
        "success_rate": round(success / len(rows) * 100, 2),
        "stages": stages,
    }


@router.get("/web-analytics")
def get_web_analytics(
    days: int = Query(default=30, ge=7, le=90),
    db: Session = Depends(get_db),
):
    """Web analytics time series."""
    d_to = _latest_date(db)
    d_from = d_to - timedelta(days=days - 1)
    rows = (
        db.query(WebAnalytic)
        .filter(WebAnalytic.date >= d_from, WebAnalytic.date <= d_to)
        .order_by(WebAnalytic.date)
        .all()
    )
    return {
        "series": [
            {
                "name": "Sessions",
                "data": [{"date": str(r.date), "value": r.sessions} for r in rows],
                "color": "#00D4FF",
            },
            {
                "name": "Bounce Rate",
                "data": [{"date": str(r.date), "value": round(r.bounce_rate * 100, 2)} for r in rows],
                "color": "#FF4757",
            },
        ]
    }
