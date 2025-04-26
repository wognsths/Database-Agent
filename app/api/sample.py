from fastapi import APIRouter
from core.database import schema_manager

router = APIRouter()

@router.get("/sample/{table_name}", summary="Get sample data of a table")
def get_table_sample(table_name: str, limit: int = 5):
    try:
        sample_data = schema_manager.get_table_sample_data(table_name, limit)
        return {"sample_data": sample_data}
    except Exception as e:
        return {"error": str(e)}