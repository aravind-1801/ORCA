from fastapi import APIRouter, Query, Path
from backend.app.config import settings
from backend.app.schemas.orca import (
    OrcaQueryRequest,
    OrcaQueryResponse,
    OrcaExplanationResponse,
)
from backend.app.agents.orchestrator import orchestrator
from backend.app.services.marine_service import marine_service

router = APIRouter(prefix="/orca", tags=["ORCA Multi-Agent AI"])


@router.post("/query", response_model=OrcaQueryResponse, summary="Submit natural language or voice query to ORCA Multi-Agent Orchestrator")
async def submit_orca_query(request: OrcaQueryRequest):
    return await orchestrator.process_query(request)


@router.get("/recommendation", summary="Get current synthesized ORCA recommendation")
async def get_current_recommendation(
    lat: float = Query(default=settings.DEFAULT_LATITUDE),
    lon: float = Query(default=settings.DEFAULT_LONGITUDE),
    lang: str = Query(default="en"),
):
    status_data = await marine_service.get_status(lat, lon)
    return {
        "text": status_data["recommendation"]["text"],
        "safety_status": status_data["safety"]["status"],
        "best_zone": status_data["best_zone"],
        "updated_at": status_data["updated_at"],
        "data_mode": status_data["data_mode"],
    }


@router.get("/explanation/{query_id}", response_model=OrcaExplanationResponse, summary="Get Why ORCA multi-agent explanation for a query")
async def get_query_explanation(query_id: str = Path(..., description="Unique query ID or 'latest'")):
    return await orchestrator.get_explanation(query_id)
