from typing import Annotated

from fastapi import APIRouter, Depends

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

    This endpoint uses Dependency Injection to obtain the LLMValidatorService.
    All application-specific errors are handled by the global exception handler.
    """
    return await llm_service.extract_structured_data(request)
