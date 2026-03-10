from fastapi import APIRouter, HTTPException
from src.models.schemas import ExtractionRequest, StructuredResponse
from src.services.llm_service import LLMValidatorService

router = APIRouter()
llm_service = LLMValidatorService()


@router.post("/extract", response_model=StructuredResponse, tags=["AI Extraction"])
async def extract_data(request: ExtractionRequest) -> StructuredResponse:
    """
    Endpoint to extract structured data (entities, summary, sentiment) from raw text.
    """
    try:
        return await llm_service.extract_structured_data(request)
    except Exception as e:
        # Map internal service errors to 500 Internal Server Error
        # In a real-world scenario, you might want more granular error mapping
        raise HTTPException(status_code=500, detail=str(e)) from e
