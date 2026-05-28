"""
Financial Agent — Workflow 3: Advanced Financial & Investment Analysis.

Aggregates P&L data, computes financial ratios, runs ARIMA-style
trend decomposition, generates scenario forecasts, and produces
narrative reports via Sarvam AI.
"""

import time
import logging
from datetime import datetime
from typing import Any, Optional

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from app.core.llm import get_analysis_llm
from app.core.database import SessionLocal, FinancialData, DailyMetric

logger = logging.getLogger(__name__)


# ── Financial Ratio Calculations ──────────────────────────────────────────────

def _compute_ratios(df: pd.DataFrame) -> dict[str, float]:
    """Calculate key financial ratios from P&L dataframe."""
    if df.empty:
        return {}
    latest = df.iloc[-1]
    prior = df.iloc[-13] if len(df) >= 13 else df.iloc[0]

    yoy_revenue_growth = (latest["revenue"] - prior["revenue"]) / prior["revenue"] * 100 if prior["revenue"] else 0

    return {
        "avg_gross_margin": round(df["gross_margin"].mean(), 2),
        "avg_net_margin": round(df["net_margin"].mean(), 2),
        "avg_ebitda_margin": round((df["ebitda"] / df["revenue"]).mean() * 100, 2),
        "revenue_cagr_pct": round(
            ((df["revenue"].iloc[-1] / df["revenue"].iloc[0]) ** (12 / max(len(df) - 1, 1)) - 1) * 100, 2
        ),
        "yoy_revenue_growth_pct": round(yoy_revenue_growth, 2),
        "latest_gross_margin": round(latest["gross_margin"], 2),
        "latest_net_margin": round(latest["net_margin"], 2),
        "latest_ebitda": round(latest["ebitda"], 2),
        "opex_ratio": round(latest["opex"] / latest["revenue"] * 100 if latest["revenue"] else 0, 2),
        "total_revenue_period": round(df["revenue"].sum(), 2),
        "total_net_income_period": round(df["net_income"].sum(), 2),
        "headcount_growth_pct": round(
            (df["headcount"].iloc[-1] - df["headcount"].iloc[0]) / df["headcount"].iloc[0] * 100
            if df["headcount"].iloc[0] else 0, 2
        ),
    }


# ── Forecasting ───────────────────────────────────────────────────────────────

def _forecast_series(series: pd.Series, periods: int = 6, scenario: str = "base") -> list[dict]:
    """Holt-Winters exponential smoothing forecast with scenario adjustments."""
    try:
        model = ExponentialSmoothing(
            series,
            trend="add",
            seasonal="add",
            seasonal_periods=12,
            initialization_method="estimated",
        ).fit(optimized=True)
        forecast = model.forecast(periods)
    except Exception:
        # Fallback: simple linear extrapolation
        x = np.arange(len(series))
        coeffs = np.polyfit(x, series.values, 1)
        poly = np.poly1d(coeffs)
        forecast = pd.Series([poly(len(series) + i) for i in range(periods)])

    # Scenario multipliers
    multipliers = {"bull": 1.08, "base": 1.0, "bear": 0.92}
    mult = multipliers.get(scenario, 1.0)

    # Generate future month labels
    last_idx = series.index[-1] if not series.index.empty else "2025-12"
    try:
        last_dt = datetime.strptime(str(last_idx), "%Y-%m")
    except Exception:
        last_dt = datetime(2025, 12, 1)

    result = []
    for i, val in enumerate(forecast):
        m = last_dt.month + i + 1
        y = last_dt.year + (m - 1) // 12
        m = ((m - 1) % 12) + 1
        result.append({
            "date": f"{y}-{m:02d}",
            "value": round(float(val) * mult, 2),
            "is_forecast": True,
        })
    return result


class FinancialAgent:
    """Compiles financial analysis reports with forecasting and LLM narrative."""

    def run(
        self,
        period_from: str,
        period_to: str,
        include_forecast: bool = True,
        scenario: str = "base",
    ) -> dict[str, Any]:
        start = time.time()

        db = SessionLocal()
        try:
            rows = (
                db.query(FinancialData)
                .filter(
                    FinancialData.month >= period_from,
                    FinancialData.month <= period_to,
                )
                .order_by(FinancialData.month)
                .all()
            )
        finally:
            db.close()

        if not rows:
            return {"error": f"No financial data found for {period_from} to {period_to}"}

        df = pd.DataFrame([{
            "month": r.month,
            "revenue": r.revenue,
            "cogs": r.cogs,
            "gross_profit": r.gross_profit,
            "gross_margin": r.gross_margin,
            "opex": r.opex,
            "ebitda": r.ebitda,
            "net_income": r.net_income,
            "net_margin": r.net_margin,
            "cash_flow": r.cash_flow,
            "headcount": r.headcount,
        } for r in rows])

        # Time series arrays — field names match frontend expectations
        revenue_trend = [{"period": row["month"], "revenue": row["revenue"]} for _, row in df.iterrows()]
        margin_trend = [{"period": row["month"], "gross_margin": row["gross_margin"], "net_margin": row["net_margin"]} for _, row in df.iterrows()]
        ebitda_trend = [{"period": row["month"], "ebitda": row["ebitda"]} for _, row in df.iterrows()]

        # Forecast — nested under "forecast.revenue" as frontend expects
        forecast_revenue = []
        if include_forecast and len(df) >= 12:
            revenue_series = df.set_index("month")["revenue"]
            raw = _forecast_series(revenue_series, periods=6, scenario=scenario)
            forecast_revenue = [{"period": r["date"], "forecast": r["value"]} for r in raw]

        # Financial ratios
        key_ratios = _compute_ratios(df)

        # LLM narrative
        narrative, risk_factors, opportunities = self._generate_narrative(df, key_ratios, scenario)

        return {
            "period": f"{period_from} to {period_to}",
            "narrative": narrative,
            "revenue_trend": revenue_trend,
            "margin_trend": margin_trend,
            "ebitda_trend": ebitda_trend,
            "forecast": {"revenue": forecast_revenue},
            "financial_ratios": key_ratios,
            "growth_metrics": {
                "revenue_cagr": key_ratios.get("revenue_cagr_pct", 0),
                "yoy_growth": key_ratios.get("yoy_revenue_growth_pct", 0),
            },
            "risk_factors": risk_factors,
            "opportunities": opportunities,
            "execution_time_ms": int((time.time() - start) * 1000),
        }

    def _generate_narrative(
        self,
        df: pd.DataFrame,
        ratios: dict,
        scenario: str,
    ) -> tuple[str, list[str], list[str]]:
        try:
            llm = get_analysis_llm()
            metrics_text = "\n".join([f"  • {k}: {v}" for k, v in ratios.items()])
            prompt = f"""You are a CFO-level financial analyst reviewing company performance.

Key Financial Metrics:
{metrics_text}

Scenario modeled: {scenario.upper()}
Data covers {len(df)} months.

Write a concise executive summary (3-4 sentences) and identify:
1. Top 3 financial risks
2. Top 3 growth opportunities

Format:
SUMMARY: <text>
RISKS:
- <risk1>
- <risk2>
- <risk3>
OPPORTUNITIES:
- <opp1>
- <opp2>
- <opp3>"""

            response = llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)

            narrative = "Financial performance analysis complete."
            risk_factors = ["Monitor margin compression", "Watch operating expense growth", "Currency exposure risk"]
            opportunities = ["Revenue expansion potential", "Headcount optimization", "New market entry"]

            if "SUMMARY:" in content:
                parts = content.split("SUMMARY:", 1)[1]
                if "RISKS:" in parts:
                    s_part, rest = parts.split("RISKS:", 1)
                    narrative = s_part.strip()
                    if "OPPORTUNITIES:" in rest:
                        r_part, o_part = rest.split("OPPORTUNITIES:", 1)
                        risk_factors = [r.strip().lstrip("- ") for r in r_part.strip().split("\n") if r.strip().startswith("-")][:3]
                        opportunities = [o.strip().lstrip("- ") for o in o_part.strip().split("\n") if o.strip().startswith("-")][:3]
            return narrative, risk_factors, opportunities
        except Exception as e:
            logger.error("Financial narrative failed: %s", e)
            return "Financial analysis complete.", ["Monitor cash flow"], ["Expand product offerings"]

    async def run_async(self, period_from: str, period_to: str, include_forecast: bool = True, scenario: str = "base") -> dict[str, Any]:
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.run, period_from, period_to, include_forecast, scenario)
