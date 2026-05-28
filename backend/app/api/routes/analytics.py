"""Analytics API — natural language queries, RCA, financial, and insight endpoints."""

import logging
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.orm import Session

from app.models.schemas import (
    AnalyticsQueryRequest,
    AnalyticsQueryResponse,
    RCARequest,
    RCAResponse,
    FinancialReportRequest,
    FinancialReportResponse,
    InsightRequest,
    InsightReport,
)
from app.agents import TextToSQLAgent, RootCauseAgent, FinancialAgent, InsightAgent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

_bi = TextToSQLAgent()
_rca = RootCauseAgent()
_fin = FinancialAgent()
_insight = InsightAgent()


@router.post("/query", response_model=AnalyticsQueryResponse)
async def run_query(request: AnalyticsQueryRequest):
    """Convert a natural language question to SQL and return results."""
    try:
        result = await _bi.run_async(request.question)
        return AnalyticsQueryResponse(
            question=request.question,
            answer=result.get("answer", ""),
            sql_query=result.get("sql_query"),
            rows=result.get("rows"),
            chart_spec=result.get("chart_spec"),
            execution_time_ms=result.get("execution_time_ms", 0),
        )
    except Exception as e:
        logger.exception("BI query error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rca")
async def run_rca(request: RCARequest):
    """Trigger automated root cause analysis for a metric anomaly."""
    try:
        result = await _rca.run_async(
            request.metric,
            request.date_from,
            request.date_to,
            request.alert_threshold,
        )
        return result
    except Exception as e:
        logger.exception("RCA error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/financial")
async def run_financial(request: FinancialReportRequest):
    """Generate a comprehensive financial analysis report."""
    try:
        result = await _fin.run_async(
            request.period_from,
            request.period_to,
            request.include_forecast,
            request.scenario,
        )
        return result
    except Exception as e:
        logger.exception("Financial agent error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/insights")
async def run_insights(request: InsightRequest):
    """Generate an automated insight report for the specified persona."""
    try:
        result = await _insight.run_async(
            request.persona,
            request.date_from,
            request.date_to,
            request.focus_areas,
        )
        return result
    except Exception as e:
        logger.exception("Insight agent error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
def get_metrics_summary(
    metric: str = Query(default="revenue"),
    period: str = Query(default="30d"),
):
    """Return quick metric summary statistics."""
    from datetime import date, timedelta
    from app.core.database import SessionLocal, DailyMetric
    from sqlalchemy import func
    import numpy as np

    db = SessionLocal()
    try:
        days = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}.get(period, 30)
        d_to = date.today() - timedelta(days=1)
        d_from = d_to - timedelta(days=days - 1)

        col = getattr(DailyMetric, metric, DailyMetric.revenue)
        rows = db.query(col, DailyMetric.date).filter(
            DailyMetric.date >= d_from, DailyMetric.date <= d_to
        ).all()

        values = [float(r[0]) for r in rows if r[0] is not None]
        if not values:
            return {"error": f"No data for metric={metric}"}

        return {
            "metric": metric,
            "period": period,
            "count": len(values),
            "sum": round(sum(values), 2),
            "mean": round(np.mean(values), 2),
            "median": round(np.median(values), 2),
            "min": round(min(values), 2),
            "max": round(max(values), 2),
            "std": round(np.std(values), 2),
            "pct_change_wow": round(
                (np.mean(values[-7:]) - np.mean(values[-14:-7])) / np.mean(values[-14:-7]) * 100
                if len(values) >= 14 else 0, 2
            ),
        }
    finally:
        db.close()
