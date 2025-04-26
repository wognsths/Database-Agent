from typing import Any, Dict, List, Optional, Literal, AsyncIterable
from langchain_core.tools import tool
import httpx
from core.config import settings
BASE_URL = settings.BASE_URL


def request_helper(method: str, endpoint: str, **kwargs) -> Any:
    url = f"{BASE_URL}{endpoint}"
    try:
        with httpx.Client(timeout=5.0) as client:
            if method.lower() == "get":
                response = client.get(url, **kwargs)
            elif method.lower() == "post":
                response = client.post(url, **kwargs)
            else:
                raise ValueError("Unsupported HTTP method")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"error": str(e)}

@tool
def get_database_schema() -> Any:
    return request_helper("get", "/api/schema")

@tool
def get_table_list() -> Any:
    return request_helper("get", "/api/tables")

@tool
def get_table_sample(table_name: str, limit: int = 5) -> Any:
    return request_helper(
        "get",
        f"/api/sample/{table_name}?limit={limit}")

@tool
def run_custom_query(sql_query: str) -> Any:
    return request_helper("post", "/api/query", json={"query": sql_query})