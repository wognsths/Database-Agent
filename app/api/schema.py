from fastapi import APIRouter
from app.core.database import schema_manager

router = APIRouter()

@router.get("/schema", summary="Get full database schema")
def get_database_schema():
    schema = schema_manager.get_schema()
    return {"schema": schema}

@router.get("/tables", summary="Get list of tables")
def get_table_list():
    tables = schema_manager.get_tables()
    return {"tables": tables}