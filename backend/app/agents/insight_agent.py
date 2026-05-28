"""
Insight Agent — Workflow 5: Automated Insight Generation & Charting.

Scans all metrics for statistically significant patterns, generates
persona-aware narratives via Sarvam AI, selects optimal chart types,
and assembles multi-section insight reports.
"""

import time
import logging
from datetime import date, timedelta, datetime
from typing import Any, Optional

import numpy as np
import pandas as pd
from scipy import stats
from sqlalchemy import text

from app.core.database import SessionLocal, DailyMetric, FinancialData, WebAnalytic, SalesTransaction
from app.core.llm import get_analysis_llm

logger = logging.getLogger(__name__)

PERSONA_CONTEXTS = {
    "exec": "You are writing for a C-suite executive. Be concise, strategic, and focus on business impact. Avoid technical jargon.",
    "analyst": "You are writing for a business analyst. Include specific numbers, percentage changes, and analytical context.",
    "engineer": "You are writing for a data engineer. Include technical details, data quality observations, and system-level insights.",
}


def _mann_kendall_trend(series: pd.Series) -> tuple[float, str]:
    """Simple Mann-Kendall trend test. Returns (p-value, 'increasing'|'decreasing'|'no_trend')."""
    n = len(series)
    if n < 4:
        return 1.0, "no_trend"
    s = 0
    for i in range(n - 1):
        for j in range(i + 1, n):
            diff = series.iloc[j] - series.iloc[i]
            s += (1 if diff > 0 else -1 if diff < 0 else 0)
    var_s = n * (n - 1) * (2 * n + 5) / 18
    if var_s == 0:
        return 1.0, "no_trend"
    z = (s - 1) / (var_s ** 0.5) if s > 0 else (s + 1) / (var_s ** 0.5) if s < 0 else 0
    p = 2 * (1 - stats.norm.cdf(abs(z)))
    direction = "increasing" if s > 0 else "decreasing" if s < 0 else "no_trend"
    return round(p, 4), direction


def _week_over_week_change(series: pd.Series) -> float:
    """Latest week vs prior week average change."""
    if len(series) < 14:
        return 0.0
    latest_week = series.iloc[-7:].mean()
    prior_week = series.iloc[-14:-7].mean()
    if prior_week == 0:
        return 0.0
    return round((latest_week - prior_week) / prior_week * 100, 2)


def _select_chart_type(data_shape: str, n_series: int) -> str:
    """Heuristic chart type selection."""
    if data_shape == "time_series":
        return "area" if n_series == 1 else "line"
    if data_shape == "categorical_comparison":
        return "bar"
    if data_shape == "distribution":
        return "bar"
    if data_shape == "part_of_whole":
        return "pie"
    return "line"


class InsightAgent:
    """Generates automated insight reports tailored to user persona."""

    def _latest_metric_date(self) -> date:
        """Return the most recent date in DailyMetric (avoids gaps with synthetic data)."""
        db = SessionLocal()
        try:
            from sqlalchemy import func
            result = db.query(func.max(DailyMetric.date)).scalar()
            return result or date.today() - timedelta(days=1)
        finally:
            db.close()

    def run(
        self,
        persona: str = "analyst",
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        focus_areas: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        start = time.time()
        focus_areas = focus_areas or []

        # Use the latest date in the DB so synthetic data always has results
        db_latest = self._latest_metric_date()
        d_to = date.fromisoformat(date_to) if date_to else db_latest
        d_from = date.fromisoformat(date_from) if date_from else d_to - timedelta(days=90)

        # Load data
        metrics_df = self._load_daily_metrics(d_from, d_to)
        web_df = self._load_web_analytics(d_from, d_to)
        financial_df = self._load_financial(d_from)

        findings = []

        # ── Revenue Trend Analysis ────────────────────────────────────────────
        if not focus_areas or "revenue" in focus_areas:
            finding = self._analyze_revenue_trend(metrics_df, persona)
            if finding:
                findings.append(finding)

        # ── Conversion Rate Analysis ──────────────────────────────────────────
        if not focus_areas or "conversion" in focus_areas:
            finding = self._analyze_conversion(metrics_df, web_df, persona)
            if finding:
                findings.append(finding)

        # ── Customer Acquisition Analysis ─────────────────────────────────────
        if not focus_areas or "customers" in focus_areas:
            finding = self._analyze_customer_growth(metrics_df, persona)
            if finding:
                findings.append(finding)

        # ── Financial Margin Analysis ─────────────────────────────────────────
        if not focus_areas or "financial" in focus_areas:
            finding = self._analyze_margins(financial_df, persona)
            if finding:
                findings.append(finding)

        # Sort by significance
        findings.sort(key=lambda x: x.get("significance", 0), reverse=True)

        # Executive summary
        exec_summary = self._generate_executive_summary(findings, persona, d_from, d_to)

        # Recommended actions derived from findings
        recommended_actions = self._generate_recommended_actions(findings)

        return {
            "generated_at": datetime.utcnow().isoformat(),
            "persona": persona,
            "period": f"{d_from} to {d_to}",
            "executive_summary": exec_summary,
            "insights": findings,          # frontend reads "insights"
            "sections": findings,          # keep for backward compat
            "total_findings": len(findings),
            "recommended_actions": recommended_actions,
            "execution_time_ms": int((time.time() - start) * 1000),
        }

    def _load_daily_metrics(self, d_from: date, d_to: date) -> pd.DataFrame:
        db = SessionLocal()
        try:
            rows = db.query(DailyMetric).filter(
                DailyMetric.date >= d_from,
                DailyMetric.date <= d_to,
            ).order_by(DailyMetric.date).all()
            return pd.DataFrame([{
                "date": r.date, "revenue": r.revenue, "orders": r.orders,
                "sessions": r.sessions, "conversion_rate": r.conversion_rate,
                "nps": r.nps, "new_customers": r.new_customers, "avg_order_value": r.avg_order_value,
                "churn_rate": r.churn_rate,
            } for r in rows])
        finally:
            db.close()

    def _load_web_analytics(self, d_from: date, d_to: date) -> pd.DataFrame:
        db = SessionLocal()
        try:
            rows = db.query(WebAnalytic).filter(
                WebAnalytic.date >= d_from,
                WebAnalytic.date <= d_to,
            ).order_by(WebAnalytic.date).all()
            return pd.DataFrame([{
                "date": r.date, "sessions": r.sessions, "pageviews": r.pageviews,
                "bounce_rate": r.bounce_rate, "avg_session_duration": r.avg_session_duration,
            } for r in rows])
        finally:
            db.close()

    def _load_financial(self, d_from: date) -> pd.DataFrame:
        db = SessionLocal()
        try:
            month_from = d_from.strftime("%Y-%m")
            rows = db.query(FinancialData).filter(
                FinancialData.month >= month_from
            ).order_by(FinancialData.month).limit(12).all()
            return pd.DataFrame([{
                "month": r.month, "revenue": r.revenue, "gross_margin": r.gross_margin,
                "net_margin": r.net_margin, "ebitda": r.ebitda,
            } for r in rows])
        finally:
            db.close()

    def _analyze_revenue_trend(self, df: pd.DataFrame, persona: str) -> Optional[dict]:
        if df.empty or "revenue" not in df.columns:
            return None
        p_val, direction = _mann_kendall_trend(df["revenue"])
        wow = _week_over_week_change(df["revenue"])
        significance = 1 - p_val

        narrative = self._generate_narrative(
            persona,
            f"Revenue is {direction} (week-over-week: {wow:+.1f}%). Mann-Kendall p={p_val:.3f}.",
            "revenue trend",
        )

        return {
            "title": "Revenue Trend",
            "narrative": narrative,
            "finding_type": "trend",
            "significance": round(significance, 3),
            "trend": direction,
            "change_pct": round(wow, 2),
            "period": f"{df['date'].iloc[0]} to {df['date'].iloc[-1]}" if not df.empty else "",
            "chart_spec": {
                "type": "area",
                "title": "Daily Revenue Trend",
                "x_axis": "date",
                "y_axis": ["revenue"],
                "data": [{"date": str(r["date"]), "revenue": r["revenue"]} for _, r in df.iterrows()],
            },
        }

    def _analyze_conversion(self, metrics_df: pd.DataFrame, web_df: pd.DataFrame, persona: str) -> Optional[dict]:
        if metrics_df.empty:
            return None
        wow = _week_over_week_change(metrics_df["conversion_rate"])
        p_val, direction = _mann_kendall_trend(metrics_df["conversion_rate"])
        significance = max(0, 1 - p_val) if abs(wow) > 5 else 0.3

        narrative = self._generate_narrative(
            persona,
            f"Conversion rate is {direction}, week-over-week change: {wow:+.1f}%.",
            "conversion rate",
        )

        return {
            "title": "Conversion Rate Analysis",
            "narrative": narrative,
            "finding_type": "trend",
            "significance": round(significance, 3),
            "trend": direction,
            "change_pct": round(wow, 2),
            "period": f"{metrics_df['date'].iloc[0]} to {metrics_df['date'].iloc[-1]}" if not metrics_df.empty else "",
            "chart_spec": {
                "type": "line",
                "title": "Conversion Rate Over Time",
                "x_axis": "date",
                "y_axis": ["conversion_rate"],
                "data": [
                    {"date": str(r["date"]), "conversion_rate": round(r["conversion_rate"] * 100, 3)}
                    for _, r in metrics_df.iterrows()
                ],
            },
        }

    def _analyze_customer_growth(self, df: pd.DataFrame, persona: str) -> Optional[dict]:
        if df.empty or "new_customers" not in df.columns:
            return None
        wow = _week_over_week_change(df["new_customers"])
        churn_wow = _week_over_week_change(df["churn_rate"])
        significance = min(1.0, abs(wow) / 20)

        narrative = self._generate_narrative(
            persona,
            f"New customer acquisition changed {wow:+.1f}% week-over-week. Churn rate trend: {churn_wow:+.1f}%.",
            "customer acquisition and churn",
        )

        _, direction = _mann_kendall_trend(df["new_customers"])
        return {
            "title": "Customer Acquisition & Retention",
            "narrative": narrative,
            "finding_type": "trend",
            "significance": round(significance, 3),
            "trend": direction,
            "change_pct": round(wow, 2),
            "period": f"{df['date'].iloc[0]} to {df['date'].iloc[-1]}" if not df.empty else "",
            "chart_spec": {
                "type": "bar",
                "title": "New Customers vs Churn Rate",
                "x_axis": "date",
                "y_axis": ["new_customers"],
                "data": [{"date": str(r["date"]), "new_customers": r["new_customers"]} for _, r in df.iterrows()],
            },
        }

    def _analyze_margins(self, df: pd.DataFrame, persona: str) -> Optional[dict]:
        if df.empty:
            return None
        avg_gross = df["gross_margin"].mean()
        avg_net = df["net_margin"].mean()
        p_val, direction = _mann_kendall_trend(df["gross_margin"])
        significance = 1 - p_val

        narrative = self._generate_narrative(
            persona,
            f"Gross margin averages {avg_gross:.1f}%, net margin {avg_net:.1f}%. Trend: {direction}.",
            "financial margins",
        )

        return {
            "title": "Financial Margin Analysis",
            "narrative": narrative,
            "finding_type": "trend",
            "significance": round(significance, 3),
            "trend": direction,
            "change_pct": round(float(df["gross_margin"].iloc[-1] - df["gross_margin"].iloc[0]), 2) if len(df) >= 2 else 0.0,
            "period": f"{df['month'].iloc[0]} to {df['month'].iloc[-1]}" if not df.empty else "",
            "chart_spec": {
                "type": "line",
                "title": "Gross & Net Margin Trend",
                "x_axis": "month",
                "y_axis": ["gross_margin", "net_margin"],
                "data": [{"date": r["month"], "gross_margin": r["gross_margin"], "net_margin": r["net_margin"]} for _, r in df.iterrows()],
            },
        }

    def _generate_narrative(self, persona: str, finding: str, topic: str) -> str:
        try:
            llm = get_analysis_llm()
            context = PERSONA_CONTEXTS.get(persona, PERSONA_CONTEXTS["analyst"])
            prompt = f"""{context}

Write a concise 2-3 sentence insight about {topic} for a business report.
Key finding: {finding}

Be direct and actionable. Do not use bullet points."""
            response = llm.invoke(prompt)
            return response.content.strip() if hasattr(response, "content") else finding
        except Exception as e:
            logger.warning("Narrative generation failed: %s", e)
            return finding

    def _generate_recommended_actions(self, findings: list[dict]) -> list[str]:
        """Derive actionable recommendations from the findings list."""
        actions = []
        for f in findings:
            title = f.get("title", "")
            trend = f.get("trend", "no_trend")
            change = f.get("change_pct", 0)

            if "Revenue" in title:
                if trend == "decreasing" or change < -5:
                    actions.append("Investigate revenue decline drivers and launch targeted promotions.")
                else:
                    actions.append("Capitalise on revenue growth momentum with upsell campaigns.")
            elif "Conversion" in title:
                if trend == "decreasing" or change < -3:
                    actions.append("A/B test landing pages and checkout flow to recover conversion rate.")
                else:
                    actions.append("Scale top-performing acquisition channels to sustain conversion gains.")
            elif "Customer" in title:
                if change < -5:
                    actions.append("Launch churn-prevention offers for at-risk customer segments.")
                else:
                    actions.append("Expand referral and loyalty programs to accelerate customer growth.")
            elif "Margin" in title:
                actions.append("Review COGS structure and renegotiate supplier contracts for margin improvement.")

        if not actions:
            actions = [
                "Review KPI trends weekly and set automated alert thresholds.",
                "Align team OKRs with the top-priority metric improvement areas.",
            ]
        return actions[:5]

    def _generate_executive_summary(
        self, findings: list[dict], persona: str, d_from: date, d_to: date
    ) -> str:
        try:
            llm = get_analysis_llm()
            context = PERSONA_CONTEXTS.get(persona, PERSONA_CONTEXTS["analyst"])
            topics = [f["title"] for f in findings]
            prompt = f"""{context}

Write a 3-sentence executive summary for a business intelligence report covering {d_from} to {d_to}.
Topics covered: {', '.join(topics)}.
Focus on overall business health and the most critical action items."""
            response = llm.invoke(prompt)
            return response.content.strip() if hasattr(response, "content") else f"Business intelligence report for {d_from} to {d_to}."
        except Exception as e:
            logger.warning("Executive summary generation failed: %s", e)
            return f"Business intelligence report for {d_from} to {d_to}."

    async def run_async(self, persona: str, date_from: Optional[str], date_to: Optional[str], focus_areas: list[str]) -> dict[str, Any]:
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.run, persona, date_from, date_to, focus_areas)
