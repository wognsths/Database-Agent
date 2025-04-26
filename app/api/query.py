from fastapi import APIRouter
from pydantic import BaseModel
from app.core.database import db

router = APIRouter()

class QueryRequest(BaseModel):
    query: str

@router.post("/query", summary="Run a custom SQL query")
def run_query(request: QueryRequest):
    try:
        result = db.execute_query(request.query)
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}