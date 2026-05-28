"""
Text-to-SQL Agent — Workflow 1: Conversational Business Intelligence.

Direct 2-call pipeline: SQL generation → streaming interpretation.
Avoids the heavy create_sql_agent framework (which makes 4-6 LLM calls)
by doing schema-aware SQL generation in one call, executing directly via
SQLAlchemy, then streaming the interpretation as tokens arrive.
"""

import re
import json
import time
import logging
from typing import Any, Optional, Callable, Awaitable

from sqlalchemy import text
from langchain_community.utilities import SQLDatabase
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.llm import get_sql_llm
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Cached schema so we don't re-fetch on every request
_SCHEMA_CACHE: dict = {}

_SQL_SYSTEM = """You are a SQL expert. Given the database schema and a business question, write a single optimised SQLite SQL query.

Rules:
- Return ONLY the SQL statement — no explanation, no markdown fences, no semicolon at the end
- Use SQLite syntax: strftime('%Y-%m', date) for month grouping, not DATE_TRUNC
- LIMIT large result sets to 500 rows
- Alias every aggregate clearly: SUM(amount) AS total_revenue
- For top-N queries: ORDER BY col DESC LIMIT N
"""

_INTERPRET_SYSTEM = """You are Agitator Rye, an expert business intelligence assistant.
Interpret the SQL query results and answer the user's question concisely.
- Lead with the key insight in 1-2 sentences
- Highlight the top 3 findings with specific numbers
- Format currency as $X,XXX and percentages to 2 decimal places
- End with one actionable recommendation
Keep the total response under 200 words."""


def _extract_sql(raw: str) -> str:
    """Strip markdown fences and pull out the SQL statement."""
    clean = re.sub(r"```sql\s*|```", "", raw).strip()
    return clean.rstrip(";").strip()


def _smart_chart(question: str, columns: list[str], row_count: int) -> Optional[dict]:
    """
    Rule-based chart type selection — zero LLM calls.
    Heuristics based on question keywords and result shape.
    """
    if row_count == 0 or len(columns) < 2:
        return None

    q = question.lower()
    cols_lower = [c.lower() for c in columns]

    has_time = any(k in q for k in ("trend", "over time", "month", "week", "day", "year", "quarter", "daily", "weekly", "monthly"))
    has_rank = any(k in q for k in ("top", "best", "worst", "highest", "lowest", "most", "least", "ranking"))
    has_share = any(k in q for k in ("breakdown", "share", "distribution", "proportion", "percent", "by region", "by channel", "by category", "by segment"))
    has_date_col = any(c in cols_lower for c in ("date", "month", "week", "year", "period", "quarter"))

    x = columns[0]
    y_candidates = [c for c in columns[1:] if any(k in c.lower() for k in ("revenue", "amount", "total", "count", "value", "sales", "profit", "score", "rate", "orders"))]
    y = y_candidates[0] if y_candidates else columns[1]

    if has_time or has_date_col:
        chart_type = "area"
    elif has_share and row_count <= 10:
        chart_type = "pie"
    elif has_rank or row_count <= 20:
        chart_type = "bar"
    else:
        chart_type = "table"

    return {
        "chart_type": chart_type,
        "x_axis": x,
        "y_axis": [y],
        "title": question[:60],
        "data": [],
    }


class TextToSQLAgent:
    """Direct 2-call Text-to-SQL agent with real token streaming."""

    def __init__(self):
        self._db: Optional[SQLDatabase] = None

    def _get_db(self) -> SQLDatabase:
        if self._db is None:
            self._db = SQLDatabase.from_uri(
                settings.database_url,
                include_tables=[
                    "sales_transactions", "customers", "products",
                    "daily_metrics", "financial_data", "web_analytics",
                    "anomaly_events",
                ],
                sample_rows_in_table_info=2,
            )
        return self._db

    def _get_schema(self) -> str:
        if "schema" not in _SCHEMA_CACHE:
            _SCHEMA_CACHE["schema"] = self._get_db().get_table_info()
        return _SCHEMA_CACHE["schema"]

    def _execute_sql(self, sql: str) -> tuple[list[dict], list[str], Optional[str]]:
        """Execute SQL directly via SQLAlchemy and return (rows, columns, error)."""
        from app.core.database import SessionLocal
        db_session = SessionLocal()
        try:
            result = db_session.execute(text(sql))
            columns = list(result.keys())
            rows = [dict(zip(columns, row)) for row in result.fetchall()]
            return rows, columns, None
        except Exception as exc:
            return [], [], str(exc)
        finally:
            db_session.close()

    async def run_streaming(
        self,
        question: str,
        send_token: Callable[[str], Awaitable[None]],
    ) -> dict[str, Any]:
        """
        Full pipeline with real LLM token streaming.

        Steps:
          1. Generate SQL  (1 LLM call, no streaming — fast)
          2. Execute SQL   (direct SQLAlchemy — no LLM)
          3. Retry once on SQL error with error feedback
          4. Stream interpretation tokens as they arrive
          5. Build chart spec via rules  (0 extra LLM calls)
        """
        start = time.time()
        llm = get_sql_llm()
        schema = self._get_schema()

        # ── 1. SQL generation ──────────────────────────────────────────────
        sql_messages = [
            SystemMessage(content=_SQL_SYSTEM),
            HumanMessage(content=f"Schema:\n{schema}\n\nQuestion: {question}\n\nSQL:"),
        ]
        try:
            sql_resp = await llm.ainvoke(sql_messages)
            sql = _extract_sql(sql_resp.content)
        except Exception as exc:
            msg = f"SQL generation failed: {exc}"
            await send_token(msg)
            return {"answer": msg, "sql_query": None, "rows": None, "chart_spec": None,
                    "execution_time_ms": int((time.time() - start) * 1000)}

        # ── 2. Execute ─────────────────────────────────────────────────────
        rows, columns, sql_error = self._execute_sql(sql)

        # ── 3. Self-heal on error (one retry) ─────────────────────────────
        if sql_error:
            fix_messages = [
                SystemMessage(content=_SQL_SYSTEM),
                HumanMessage(content=(
                    f"Schema:\n{schema}\n\nQuestion: {question}\n\n"
                    f"The following SQL failed:\n{sql}\n\nError: {sql_error}\n\nCorrected SQL:"
                )),
            ]
            try:
                fix_resp = await llm.ainvoke(fix_messages)
                sql = _extract_sql(fix_resp.content)
                rows, columns, sql_error = self._execute_sql(sql)
            except Exception:
                pass

        # ── 4. Stream interpretation ───────────────────────────────────────
        if rows:
            result_summary = (
                f"Query returned {len(rows)} rows. Columns: {', '.join(columns)}.\n"
                f"First 5 rows:\n{json.dumps(rows[:5], default=str)}"
            )
        else:
            result_summary = (
                "The query returned no results."
                + (f" SQL error: {sql_error}" if sql_error else "")
            )

        interp_messages = [
            SystemMessage(content=_INTERPRET_SYSTEM),
            HumanMessage(content=(
                f"User question: {question}\n\nSQL executed:\n{sql}\n\n{result_summary}"
            )),
        ]

        answer_parts: list[str] = []
        try:
            async for chunk in llm.astream(interp_messages):
                token = chunk.content
                if token:
                    answer_parts.append(token)
                    await send_token(token)
        except Exception as exc:
            fallback = f"Query returned {len(rows)} result(s)."
            answer_parts.append(fallback)
            await send_token(fallback)
            logger.warning("Interpretation stream error: %s", exc)

        answer = "".join(answer_parts)

        # ── 5. Chart spec (rule-based, no LLM) ────────────────────────────
        chart_spec = None
        if rows and columns:
            spec = _smart_chart(question, columns, len(rows))
            if spec:
                spec["data"] = rows[:500]
                chart_spec = spec

        return {
            "answer": answer,
            "sql_query": sql,
            "rows": rows[:200] if rows else None,
            "chart_spec": chart_spec,
            "execution_time_ms": int((time.time() - start) * 1000),
        }

    async def run_async(self, question: str) -> dict[str, Any]:
        """Async run without streaming (used by REST endpoint)."""
        tokens: list[str] = []

        async def collect(t: str) -> None:
            tokens.append(t)

        return await self.run_streaming(question, collect)

    def run(self, question: str) -> dict[str, Any]:
        """Sync run (kept for compatibility)."""
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self.run_async(question))
        finally:
            loop.close()
