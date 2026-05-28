"""Chat API — WebSocket streaming endpoint + REST fallback."""

import json
import uuid
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse

from app.models.schemas import ChatRequest, ChatResponse
from app.agents import TextToSQLAgent, RootCauseAgent, FinancialAgent, PipelineAgent, InsightAgent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["Chat"])

# Singletons (reuse across requests for connection pooling)
_bi_agent = TextToSQLAgent()
_rca_agent = RootCauseAgent()
_fin_agent = FinancialAgent()
_pipeline_agent = PipelineAgent()
_insight_agent = InsightAgent()

AGENT_MAP = {
    "bi": _bi_agent,
    "rca": _rca_agent,
    "financial": _fin_agent,
    "pipeline": _pipeline_agent,
    "insight": _insight_agent,
}


@router.websocket("/ws/{session_id}")
async def chat_websocket(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for streaming AI agent responses.
    
    Message format (send):
        {"message": "...", "agent": "bi|rca|financial|pipeline|insight"}
    
    Message format (receive):
        {"type": "token", "content": "..."} — streaming tokens
        {"type": "done", "data": {...}}     — final structured response
        {"type": "error", "message": "..."} — error
    """
    await websocket.accept()
    logger.info("WebSocket connected: session=%s", session_id)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON payload"})
                continue

            message = payload.get("message", "").strip()
            agent_key = payload.get("agent", "bi")
            persona = payload.get("persona", "analyst")

            if not message:
                await websocket.send_json({"type": "error", "message": "Empty message"})
                continue

            if agent_key not in AGENT_MAP:
                await websocket.send_json({"type": "error", "message": f"Unknown agent: {agent_key}"})
                continue

            # Acknowledge start
            await websocket.send_json({"type": "start", "agent": agent_key, "session_id": session_id})

            try:
                agent = AGENT_MAP[agent_key]

                if agent_key == "bi":
                    # Real token streaming: tokens are sent as they arrive from the LLM
                    async def _send_token(token: str) -> None:
                        await websocket.send_json({"type": "token", "content": token})

                    result = await agent.run_streaming(message, _send_token)
                else:
                    # Other agents: run fully then replay tokens word-by-word
                    if agent_key == "rca":
                        result = await agent.run_async(
                            "revenue", "2025-01-01", "2025-05-28", 2.0
                        )
                    elif agent_key == "financial":
                        result = await agent.run_async("2024-01", "2025-05", True, "base")
                    elif agent_key == "pipeline":
                        result = await agent.run_async("default", "sales_transactions", {})
                    elif agent_key == "insight":
                        result = await agent.run_async(persona, None, None, [])

                    answer = (
                        result.get("answer")
                        or result.get("summary")
                        or result.get("executive_summary")
                        or ""
                    )
                    for word in answer.split():
                        await websocket.send_json({"type": "token", "content": word + " "})

                # Send final structured response
                await websocket.send_json({"type": "done", "data": result, "session_id": session_id})

            except Exception as e:
                logger.exception("Agent error in WebSocket: %s", e)
                await websocket.send_json({"type": "error", "message": str(e)})

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: session=%s", session_id)
    except Exception as e:
        logger.exception("WebSocket error: %s", e)


@router.post("/query", response_model=ChatResponse)
async def chat_query(request: ChatRequest):
    """REST fallback for agent queries (non-streaming)."""
    session_id = request.session_id or str(uuid.uuid4())
    agent_key = request.agent
    agent = AGENT_MAP.get(agent_key)

    if not agent:
        raise HTTPException(status_code=400, detail=f"Unknown agent: {agent_key}")

    try:
        if agent_key == "bi":
            result = await agent.run_async(request.message)
        elif agent_key == "rca":
            result = await agent.run_async("revenue", "2025-01-01", "2025-05-28", 2.0)
        elif agent_key == "financial":
            result = await agent.run_async("2024-01", "2025-05", True, "base")
        elif agent_key == "pipeline":
            result = await agent.run_async("default", "sales_transactions", {})
        else:
            result = await agent.run_async(request.persona or "analyst", None, None, [])

        answer = (
            result.get("answer")
            or result.get("summary")
            or result.get("executive_summary")
            or "Analysis complete."
        )

        return ChatResponse(
            session_id=session_id,
            agent=agent_key,
            answer=answer,
            sql_query=result.get("sql_query"),
            chart_spec=result.get("chart_spec"),
            table_data=result.get("rows"),
            execution_time_ms=result.get("execution_time_ms", 0),
        )
    except Exception as e:
        logger.exception("Chat query error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
