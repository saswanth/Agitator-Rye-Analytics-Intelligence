"""
Root Cause Analysis Agent — Workflow 2: Automated Root Cause Analysis.

When a KPI anomaly is detected, this agent slices the data across multiple
dimensions, scores each slice using z-scores, generates hypotheses via
Sarvam AI, and produces a structured RCA report.
"""

import time
import logging
from datetime import date, timedelta
from typing import Any, Optional

import numpy as np
import pandas as pd
from langchain_core.messages import SystemMessage

from app.core.llm import get_llm
from app.core.database import SessionLocal, SalesTransaction, DailyMetric

logger = logging.getLogger(__name__)


# ── Dimension Slicer Tools ────────────────────────────────────────────────────

def _load_metric_df(metric: str, date_from: date, date_to: date) -> pd.DataFrame:
    """Load daily metric data as a DataFrame."""
    db = SessionLocal()
    try:
        rows = (
            db.query(DailyMetric)
            .filter(DailyMetric.date >= date_from, DailyMetric.date <= date_to)
            .all()
        )
        data = [
            {
                "date": r.date,
                "value": getattr(r, metric, r.revenue),
            }
            for r in rows
        ]
        return pd.DataFrame(data)
    finally:
        db.close()


def _load_sales_df(date_from: date, date_to: date) -> pd.DataFrame:
    """Load sales transactions as DataFrame."""
    db = SessionLocal()
    try:
        rows = (
            db.query(SalesTransaction)
            .filter(
                SalesTransaction.date >= date_from,
                SalesTransaction.date <= date_to,
            )
            .all()
        )
        return pd.DataFrame([{
            "date": r.date,
            "amount": r.amount,
            "region": r.region,
            "channel": r.channel,
            "category": r.category,
            "country": r.country,
            "quantity": r.quantity,
            "profit": r.profit,
        } for r in rows])
    finally:
        db.close()


def _z_score_slice(df: pd.DataFrame, group_col: str, value_col: str) -> list[dict]:
    """Score each group value using z-score relative to all groups."""
    if df.empty or group_col not in df.columns:
        return []

    grouped = df.groupby(group_col)[value_col].sum().reset_index()
    grouped.columns = [group_col, "total"]
    mean = grouped["total"].mean()
    std = grouped["total"].std()
    if std == 0:
        return []

    grouped["z_score"] = (grouped["total"] - mean) / std
    grouped["expected"] = mean
    grouped = grouped.reindex(grouped["z_score"].abs().sort_values(ascending=False).index)
    return grouped.head(5).to_dict("records")


def _contribution_pct(slices: list[dict], value_col: str = "total") -> list[dict]:
    total = sum(abs(s[value_col]) for s in slices) or 1
    for s in slices:
        s["contribution_pct"] = round(abs(s[value_col]) / total * 100, 2)
    return slices


class RootCauseAgent:
    """Automated root cause analysis across multiple dimensions."""

    DIMENSIONS = ["region", "channel", "category", "country"]

    def run(self, metric: str, date_from: str, date_to: str, alert_threshold: float = 2.0) -> dict[str, Any]:
        start = time.time()
        try:
            d_from = date.fromisoformat(date_from)
            d_to = date.fromisoformat(date_to)
        except ValueError:
            return {"error": "Invalid date format. Use YYYY-MM-DD."}

        # Load data for the alert window and a baseline window before it
        baseline_days = (d_to - d_from).days + 1
        baseline_from = d_from - timedelta(days=baseline_days * 3)

        sales_alert = _load_sales_df(d_from, d_to)
        sales_baseline = _load_sales_df(baseline_from, d_from - timedelta(days=1))

        if sales_alert.empty:
            return {"error": "No data found for the specified period."}

        # Slice across all dimensions
        findings = []
        for dim in self.DIMENSIONS:
            alert_slices = _z_score_slice(sales_alert, dim, "amount")
            for s in alert_slices:
                findings.append({
                    "dimension": dim,
                    "dimension_value": str(s[dim]),
                    "actual": round(s["total"], 2),
                    "expected": round(s["expected"], 2),
                    "z_score": round(s["z_score"], 3),
                    "contribution_pct": 0,
                })

        # Rank by absolute z-score
        findings.sort(key=lambda x: abs(x["z_score"]), reverse=True)
        top_findings = findings[:8]

        # Calculate contribution percentages
        total_actual = sum(f["actual"] for f in top_findings) or 1
        for f in top_findings:
            f["contribution_pct"] = round(abs(f["actual"]) / total_actual * 100, 2)
            f["confidence"] = min(1.0, abs(f["z_score"]) / 5.0)

        # Filter to anomalous slices
        anomalous = [f for f in top_findings if abs(f["z_score"]) >= alert_threshold]

        # Generate narrative via LLM
        summary, recommendations = self._generate_narrative(metric, anomalous, d_from, d_to)

        # Build chart spec for top contributing dimension
        chart_spec = None
        if anomalous:
            chart_spec = {
                "chart_type": "bar",
                "title": f"Root Cause Analysis — {metric} anomaly breakdown",
                "x_axis": "dimension_value",
                "y_axis": ["actual", "expected"],
                "data": [
                    {
                        "dimension_value": f"{f['dimension']}:{f['dimension_value']}",
                        "actual": f["actual"],
                        "expected": f["expected"],
                        "z_score": f["z_score"],
                    }
                    for f in anomalous[:10]
                ],
            }

        return {
            "metric": metric,
            "period": f"{date_from} to {date_to}",
            "summary": summary,
            "root_causes": anomalous,
            "recommended_actions": recommendations,
            "confidence_score": round(
                np.mean([f["confidence"] for f in anomalous]) if anomalous else 0.0, 3
            ),
            "chart_spec": chart_spec,
            "execution_time_ms": int((time.time() - start) * 1000),
        }

    def _generate_narrative(
        self,
        metric: str,
        findings: list[dict],
        d_from: date,
        d_to: date,
    ) -> tuple[str, list[str]]:
        """Use Sarvam AI to generate the root cause narrative and recommendations."""
        try:
            llm = get_llm()
            findings_text = "\n".join([
                f"  • {f['dimension'].title()} = {f['dimension_value']}: "
                f"actual={f['actual']:,.0f}, expected={f['expected']:,.0f}, "
                f"z-score={f['z_score']:.2f}, contributes {f['contribution_pct']:.1f}%"
                for f in findings
            ])
            prompt = f"""You are an expert business analyst. A metric anomaly was detected:

Metric: {metric}
Period: {d_from} to {d_to}

Top contributing slices:
{findings_text or 'No significant slices found.'}

Write:
1. A concise executive summary (2-3 sentences) explaining the root cause
2. Three specific, actionable recommendations

Format:
SUMMARY: <text>
RECOMMENDATIONS:
- <rec1>
- <rec2>
- <rec3>"""

            response = llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)

            # Parse summary and recommendations
            summary = metric + " anomaly detected."
            recs = ["Investigate the flagged dimension", "Review recent changes", "Monitor closely"]
            if "SUMMARY:" in content:
                parts = content.split("SUMMARY:", 1)
                rest = parts[1]
                if "RECOMMENDATIONS:" in rest:
                    summary_part, rec_part = rest.split("RECOMMENDATIONS:", 1)
                    summary = summary_part.strip()
                    recs = [
                        r.strip().lstrip("- ").strip()
                        for r in rec_part.strip().split("\n")
                        if r.strip().startswith("-")
                    ][:5]
            return summary, recs
        except Exception as e:
            logger.error("RCA narrative generation failed: %s", e)
            return f"Anomaly detected in {metric} for period {d_from} to {d_to}.", [
                "Review the flagged dimension values",
                "Compare with historical baselines",
                "Escalate if the pattern persists",
            ]

    async def run_async(self, metric: str, date_from: str, date_to: str, threshold: float = 2.0) -> dict[str, Any]:
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.run, metric, date_from, date_to, threshold)
