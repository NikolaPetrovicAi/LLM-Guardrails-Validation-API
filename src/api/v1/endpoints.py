from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from src.api.deps import get_llm_service
from src.models.schemas import (
    ExtractionRequest,
    ScriptRequest,
    StructuredResponse,
    ViralScriptResponse,
)
from src.services.llm_service import ViralContentService

router = APIRouter()


@router.post("/extract", response_model=StructuredResponse, tags=["Legacy"])
async def extract_structured_data(
    request: ExtractionRequest,
    llm_service: Annotated[ViralContentService, Depends(get_llm_service)],
) -> StructuredResponse:
    """
    Legacy endpoint for structured data extraction.
    Maintained for compatibility with existing LLM-as-a-Judge tests.
    """
    return await llm_service.extract_legacy_data(request)


@router.post("/generate", response_model=ViralScriptResponse, tags=["Viral Content"])
async def generate_script(
    request: ScriptRequest,
    llm_service: Annotated[ViralContentService, Depends(get_llm_service)],
) -> ViralScriptResponse:
    """
    Endpoint to generate a viral video script and audit from topic and audience.
    """
    return await llm_service.generate_viral_script(request)


@router.post("/generate-stream", tags=["Viral Content"])
async def generate_script_stream(
    request: ScriptRequest,
    llm_service: Annotated[ViralContentService, Depends(get_llm_service)],
) -> StreamingResponse:
    """
    Endpoint to stream viral script generation in real-time.
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        async for partial in llm_service.stream_viral_script(request):
            yield f"data: {partial.model_dump_json()}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/health", tags=["Health"])
async def health_check(
    llm_service: Annotated[ViralContentService, Depends(get_llm_service)],
) -> dict:
    """
    Check the health of the LLM provider and cache.
    """
    is_healthy = await llm_service.check_health()
    if not is_healthy:
        return {"status": "unhealthy", "details": "LLM Provider or Cache unreachable"}
    return {"status": "healthy"}
