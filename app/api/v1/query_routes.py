from fastapi import APIRouter, Depends
from services.llm_service import generate_real_estate_response
from schemas.query_schema import QueryRequest

router = APIRouter()

@router.post("/query")
def query_llm(request: QueryRequest):
    answer = generate_real_estate_response(request.question)
    return {"answer": answer}