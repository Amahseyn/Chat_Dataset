from fastapi import APIRouter
from schemas.query_schema import QueryRequest
from services.llm_service import generate_real_estate_response

router = APIRouter()

@router.post("/chat")
def chat_with_agent(request: QueryRequest):
    answer = generate_real_estate_response(request.question)
    return {"answer": answer}