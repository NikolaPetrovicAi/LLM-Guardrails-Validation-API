from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from src.api.deps import get_llm_service
from src.models.schemas import ExtractionRequest, StructuredResponse
from src.services.llm_service import LLMValidatorService

router = APIRouter()


@router.post("/extract", response_model=StructuredResponse, tags=["AI Extraction"])
async def extract_data(
    request: ExtractionRequest,
    llm_service: Annotated[LLMValidatorService, Depends(get_llm_service)],
) -> StructuredResponse:
    """
    Endpoint to extract structured data (entities, summary, sentiment) from raw text.
    """
    return await llm_service.extract_structured_data(request)


@router.post("/extract-stream", tags=["AI Extraction"])
async def extract_data_stream(
    request: ExtractionRequest,
    llm_service: Annotated[LLMValidatorService, Depends(get_llm_service)],
) -> StreamingResponse:
    """
    Endpoint to stream structured data in real-time as it's being generated.
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        async for partial in llm_service.stream_structured_data(request):
            # Yield as JSON string for each update
            yield f"data: {partial.model_dump_json()}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/health", tags=["Health"])
async def health_check(
    llm_service: Annotated[LLMValidatorService, Depends(get_llm_service)],
) -> dict:
    """
    Check the health of the LLM provider and cache.
    """
    is_healthy = await llm_service.check_health()
    if not is_healthy:
        return {"status": "unhealthy", "details": "LLM Provider or Cache unreachable"}
    return {"status": "healthy"}

