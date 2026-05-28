"""Pipeline management API — trigger runs, view logs, get health."""

import logging
from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import PipelineRunRequest, PipelineRunResponse
from app.agents import PipelineAgent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/pipeline", tags=["Pipeline"])

_pipeline = PipelineAgent()


@router.post("/run", response_model=PipelineRunResponse)
async def run_pipeline(request: PipelineRunRequest):
    """Trigger a data cleaning and validation pipeline run."""
    try:
        result = await _pipeline.run_async(
            request.pipeline_name,
            request.target_table,
            request.strategies,
        )
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return PipelineRunResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Pipeline run error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs")
def get_pipeline_logs(limit: int = Query(default=50, ge=1, le=500)):
    """Retrieve recent pipeline audit logs."""
    try:
        logs = _pipeline.get_logs(limit=limit)
        return {"logs": logs, "count": len(logs)}
    except Exception as e:
        logger.exception("Pipeline logs error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tables")
def list_tables():
    """List available tables for pipeline processing."""
    return {
        "tables": [
            {"name": "sales_transactions", "rows_approx": 150000, "description": "All sales transaction records"},
            {"name": "customers", "rows_approx": 15000, "description": "Customer profiles"},
            {"name": "products", "rows_approx": 500, "description": "Product catalog"},
            {"name": "daily_metrics", "rows_approx": 1825, "description": "Daily KPI metrics"},
            {"name": "financial_data", "rows_approx": 60, "description": "Monthly P&L statements"},
            {"name": "web_analytics", "rows_approx": 1825, "description": "Daily web analytics"},
        ]
    }
