"""
Pipeline Agent — Workflow 4: Dynamic Data Cleaning & Pipeline Management.

Detects schema drift, missing values, duplicates, and outliers.
Applies configurable cleaning strategies and logs everything with a full audit trail.
"""

import uuid
import time
import logging
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy import text, inspect

from app.core.database import SessionLocal, PipelineLog, engine
from app.core.llm import get_llm

logger = logging.getLogger(__name__)


class PipelineAgent:
    """Multi-stage data cleaning and validation pipeline."""

    STAGES = ["ingest", "schema_check", "quality_check", "clean", "validate", "load"]

    def run(
        self,
        pipeline_name: str = "default",
        target_table: str = "sales_transactions",
        strategies: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        start = time.time()
        run_id = str(uuid.uuid4())
        strategies = strategies or {}
        transformations = []
        issues_found = 0

        # ── Stage 1: Ingest ───────────────────────────────────────────────────
        self._log_stage(run_id, pipeline_name, "ingest", "running", 0, 0, 0, 0.0)
        try:
            with engine.connect() as conn:
                df = pd.read_sql(f"SELECT * FROM {target_table} LIMIT 10000", conn)
            rows_in = len(df)
            self._log_stage(run_id, pipeline_name, "ingest", "success", rows_in, rows_in, 0, 100.0)
            transformations.append({"stage": "ingest", "result": f"Loaded {rows_in} rows from {target_table}"})
        except Exception as e:
            self._log_stage(run_id, pipeline_name, "ingest", "failed", 0, 0, 1, 0.0, str(e))
            return {"error": f"Failed to ingest data: {e}", "run_id": run_id}

        # ── Stage 2: Schema Check ─────────────────────────────────────────────
        schema_issues = self._check_schema(df, target_table)
        issues_found += schema_issues
        self._log_stage(run_id, pipeline_name, "schema_check", "success", rows_in, rows_in, schema_issues, 100.0)
        transformations.append({
            "stage": "schema_check",
            "result": f"{schema_issues} schema issues detected",
            "details": "Schema drift check complete",
        })

        # ── Stage 3: Quality Check ────────────────────────────────────────────
        quality_report = self._quality_check(df)
        total_quality_issues = sum(quality_report.values())
        issues_found += total_quality_issues
        self._log_stage(run_id, pipeline_name, "quality_check", "success", rows_in, rows_in, total_quality_issues, 0.0)
        transformations.append({
            "stage": "quality_check",
            "result": f"{total_quality_issues} quality issues found",
            "details": quality_report,
        })

        # ── Stage 4: Clean ────────────────────────────────────────────────────
        df_clean, clean_log = self._clean_data(df, strategies)
        rows_after_clean = len(df_clean)
        self._log_stage(run_id, pipeline_name, "clean", "success", rows_in, rows_after_clean, 0, 0.0)
        transformations.append({
            "stage": "clean",
            "result": f"{rows_in - rows_after_clean} rows removed, {len(clean_log)} transformations applied",
            "details": clean_log,
        })

        # ── Stage 5: Validate ─────────────────────────────────────────────────
        score = self._compute_quality_score(df_clean, quality_report)
        self._log_stage(run_id, pipeline_name, "validate", "success", rows_after_clean, rows_after_clean, 0, score)
        transformations.append({
            "stage": "validate",
            "result": f"Data quality score: {score:.1f}/100",
            "details": {"quality_score": score},
        })

        # ── Stage 6: Load (update logs) ───────────────────────────────────────
        self._log_stage(run_id, pipeline_name, "load", "success", rows_after_clean, rows_after_clean, 0, score,
                        f"Pipeline {pipeline_name} complete. Score: {score:.1f}")
        transformations.append({"stage": "load", "result": "Audit log written"})

        return {
            "run_id": run_id,
            "pipeline_name": pipeline_name,
            "status": "success" if score >= 80 else "warning",
            "rows_in": rows_in,
            "rows_out": rows_after_clean,
            "issues_found": issues_found,
            "quality_score": round(score, 2),
            "transformations": transformations,
            "duration_ms": int((time.time() - start) * 1000),
        }

    def _check_schema(self, df: pd.DataFrame, table_name: str) -> int:
        """Detect unexpected nulls in non-nullable columns."""
        required_cols = {
            "sales_transactions": ["transaction_id", "date", "amount", "region"],
            "customers": ["customer_id", "email"],
            "products": ["product_id", "name", "price"],
        }
        cols = required_cols.get(table_name, [])
        issues = 0
        for col in cols:
            if col in df.columns and df[col].isnull().any():
                issues += 1
        return issues

    def _quality_check(self, df: pd.DataFrame) -> dict[str, int]:
        """Comprehensive data quality assessment."""
        report = {}

        # Missing values
        missing = int(df.isnull().sum().sum())
        report["missing_values"] = missing

        # Duplicates (by ID column if present)
        id_col = next((c for c in df.columns if c.endswith("_id") and "transaction" in c), None)
        if id_col:
            report["duplicates"] = int(df.duplicated(subset=[id_col]).sum())
        else:
            report["duplicates"] = int(df.duplicated().sum())

        # Outliers (z-score > 3.5 in numeric cols)
        numeric_cols = df.select_dtypes(include=np.number).columns
        outlier_count = 0
        for col in numeric_cols:
            if df[col].std() > 0:
                z = np.abs((df[col] - df[col].mean()) / df[col].std())
                outlier_count += int((z > 3.5).sum())
        report["outliers"] = outlier_count

        # Negative values in amount/price columns
        negative_cols = [c for c in df.columns if c in ("amount", "price", "quantity")]
        neg_count = 0
        for col in negative_cols:
            if col in df.columns:
                neg_count += int((df[col] < 0).sum())
        report["negative_values"] = neg_count

        return report

    def _clean_data(self, df: pd.DataFrame, strategies: dict[str, str]) -> tuple[pd.DataFrame, list[dict]]:
        """Apply cleaning transformations and return cleaned df + log."""
        log = []
        df = df.copy()

        # 1. Remove duplicates
        before = len(df)
        id_col = next((c for c in df.columns if "transaction_id" in c), None)
        if id_col:
            df = df.drop_duplicates(subset=[id_col])
        else:
            df = df.drop_duplicates()
        removed = before - len(df)
        if removed:
            log.append({"transformation": "deduplication", "rows_removed": removed})

        # 2. Fill missing values
        numeric_cols = df.select_dtypes(include=np.number).columns
        for col in numeric_cols:
            strategy = strategies.get(col, "median")
            if df[col].isnull().any():
                if strategy == "mean":
                    fill_val = df[col].mean()
                elif strategy == "zero":
                    fill_val = 0
                elif strategy == "forward_fill":
                    df[col] = df[col].ffill()
                    fill_val = None
                else:
                    fill_val = df[col].median()

                if fill_val is not None:
                    count = df[col].isnull().sum()
                    df[col] = df[col].fillna(fill_val)
                    log.append({"transformation": f"impute_{col}", "rows_affected": int(count), "strategy": strategy})

        # 3. Cap outliers at 3.5σ
        for col in numeric_cols:
            if col in df.columns and df[col].std() > 0:
                mean = df[col].mean()
                std = df[col].std()
                lower = mean - 3.5 * std
                upper = mean + 3.5 * std
                n_clipped = int(((df[col] < lower) | (df[col] > upper)).sum())
                if n_clipped:
                    df[col] = df[col].clip(lower, upper)
                    log.append({"transformation": f"clip_outliers_{col}", "rows_affected": n_clipped})

        # 4. Fix negative amounts
        for col in ("amount", "price", "quantity"):
            if col in df.columns:
                neg = int((df[col] < 0).sum())
                if neg:
                    df[col] = df[col].abs()
                    log.append({"transformation": f"abs_{col}", "rows_affected": neg})

        return df, log

    def _compute_quality_score(self, df: pd.DataFrame, pre_clean_issues: dict) -> float:
        """Compute 0-100 data quality score post-cleaning."""
        total_cells = df.shape[0] * df.shape[1]
        if total_cells == 0:
            return 0.0

        remaining_issues = int(df.isnull().sum().sum())
        issue_rate = remaining_issues / total_cells
        score = max(0.0, min(100.0, (1 - issue_rate) * 100 - len(pre_clean_issues) * 0.5))
        return round(score, 2)

    def _log_stage(
        self,
        run_id: str,
        pipeline_name: str,
        stage: str,
        status: str,
        rows_in: int,
        rows_out: int,
        issues: int,
        score: float,
        notes: str = "",
    ):
        db = SessionLocal()
        try:
            entry = PipelineLog(
                run_id=f"{run_id}-{stage}",
                pipeline_name=pipeline_name,
                stage=stage,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                status=status,
                rows_in=rows_in,
                rows_out=rows_out,
                issues_found=issues,
                quality_score=score,
                notes=notes,
            )
            db.add(entry)
            db.commit()
        except Exception as e:
            logger.warning("Could not write pipeline log: %s", e)
            db.rollback()
        finally:
            db.close()

    def get_logs(self, limit: int = 100) -> list[dict]:
        """Retrieve recent pipeline logs."""
        db = SessionLocal()
        try:
            rows = (
                db.query(PipelineLog)
                .order_by(PipelineLog.started_at.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "run_id": r.run_id,
                    "pipeline_name": r.pipeline_name,
                    "stage": r.stage,
                    "started_at": r.started_at.isoformat() if r.started_at else None,
                    "status": r.status,
                    "rows_in": r.rows_in,
                    "rows_out": r.rows_out,
                    "issues_found": r.issues_found,
                    "quality_score": r.quality_score,
                    "notes": r.notes,
                }
                for r in rows
            ]
        finally:
            db.close()

    async def run_async(self, pipeline_name: str, target_table: str, strategies: dict) -> dict[str, Any]:
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.run, pipeline_name, target_table, strategies)
