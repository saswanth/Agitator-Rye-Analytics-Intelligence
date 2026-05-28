"""Pydantic schemas for all API request and response models."""

from __future__ import annotations
from datetime import date, datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


# ── Chat ─────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4096)
    agent: str = Field(default="bi", pattern="^(bi|rca|financial|pipeline|insight)$")
    session_id: Optional[str] = None
    persona: Optional[str] = Field(default="analyst", pattern="^(exec|analyst|engineer)$")


class ChatResponse(BaseModel):
    session_id: str
    agent: str
    answer: str
    sql_query: Optional[str] = None
    chart_spec: Optional[dict[str, Any]] = None
    table_data: Optional[list[dict[str, Any]]] = None
    sources: list[str] = []
    execution_time_ms: int = 0


class StreamChunk(BaseModel):
    token: str
    done: bool = False
    metadata: Optional[dict[str, Any]] = None


# ── Dashboard ─────────────────────────────────────────────────────────────────

class KPICard(BaseModel):
    title: str
    value: float
    formatted_value: str
    delta: float
    delta_label: str
    trend: str  # "up" | "down" | "neutral"
    icon: str


class TimeSeriesPoint(BaseModel):
    date: str
    value: float
    label: Optional[str] = None


class ChartSeries(BaseModel):
    name: str
    data: list[TimeSeriesPoint]
    color: Optional[str] = None


class BarDataPoint(BaseModel):
    name: str
    value: float
    color: Optional[str] = None


class DashboardKPIs(BaseModel):
    kpis: list[KPICard]
    last_updated: datetime


class SalesTrendResponse(BaseModel):
    series: list[ChartSeries]
    period: str


class RevenueBreakdownResponse(BaseModel):
    by_region: list[BarDataPoint]
    by_channel: list[BarDataPoint]
    by_category: list[BarDataPoint]


class AnomalyAlertResponse(BaseModel):
    event_id: str
    metric: str
    severity: str
    actual_value: float
    expected_value: float
    z_score: float
    detected_at: datetime
    status: str
    dimension: Optional[str] = None
    dimension_value: Optional[str] = None


class PipelineHealthResponse(BaseModel):
    overall_score: float
    last_run: Optional[datetime]
    total_runs: int
    success_rate: float
    stages: list[dict[str, Any]]


# ── Analytics ─────────────────────────────────────────────────────────────────

class AnalyticsQueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)
    output_format: str = Field(default="auto", pattern="^(auto|table|chart|text)$")


class AnalyticsQueryResponse(BaseModel):
    question: str
    answer: str
    sql_query: Optional[str] = None
    rows: Optional[list[dict[str, Any]]] = None
    chart_spec: Optional[dict[str, Any]] = None
    execution_time_ms: int = 0


class RCARequest(BaseModel):
    metric: str
    date_from: str
    date_to: str
    alert_threshold: float = 2.0


class RCAFinding(BaseModel):
    dimension: str
    dimension_value: str
    contribution_pct: float
    z_score: float
    actual: float
    expected: float
    confidence: float


class RCAResponse(BaseModel):
    metric: str
    summary: str
    root_causes: list[RCAFinding]
    recommended_actions: list[str]
    confidence_score: float
    chart_spec: Optional[dict[str, Any]] = None


# ── Financial ─────────────────────────────────────────────────────────────────

class FinancialReportRequest(BaseModel):
    period_from: str  # YYYY-MM
    period_to: str
    include_forecast: bool = True
    scenario: str = Field(default="base", pattern="^(bull|base|bear)$")


class FinancialReportResponse(BaseModel):
    period: str
    executive_summary: str
    revenue_trend: list[TimeSeriesPoint]
    margin_trend: list[TimeSeriesPoint]
    ebitda_trend: list[TimeSeriesPoint]
    forecast: Optional[list[TimeSeriesPoint]] = None
    key_ratios: dict[str, float]
    risks: list[str]
    opportunities: list[str]


# ── Pipeline ──────────────────────────────────────────────────────────────────

class PipelineRunRequest(BaseModel):
    pipeline_name: str = "default"
    target_table: str = "sales_transactions"
    strategies: dict[str, str] = {}


class PipelineRunResponse(BaseModel):
    run_id: str
    status: str
    rows_in: int
    rows_out: int
    issues_found: int
    quality_score: float
    transformations: list[dict[str, Any]]
    duration_ms: int


class PipelineLogEntry(BaseModel):
    run_id: str
    pipeline_name: str
    stage: str
    started_at: datetime
    status: str
    rows_in: int
    rows_out: int
    issues_found: int
    quality_score: float


# ── Insights ──────────────────────────────────────────────────────────────────

class InsightRequest(BaseModel):
    persona: str = Field(default="analyst", pattern="^(exec|analyst|engineer)$")
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    focus_areas: list[str] = []


class InsightSection(BaseModel):
    title: str
    narrative: str
    finding_type: str   # "trend" | "anomaly" | "correlation" | "forecast"
    significance: float
    chart_spec: Optional[dict[str, Any]] = None


class InsightReport(BaseModel):
    generated_at: datetime
    persona: str
    executive_summary: str
    sections: list[InsightSection]
    total_findings: int
    period: str


# ── Generic ───────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    db_connected: bool
    llm_available: bool
    record_counts: dict[str, int]
