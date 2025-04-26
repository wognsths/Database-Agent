from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel

# Messages btw agents
class AgentMessage(BaseModel):
    sender: str
    receiver: str
    content: Dict[str, Any]
    message_type: str
    timestamp: Optional[float] = None

# User query request
class QueryRequest(BaseModel):
    query: str
    options: Optional[Dict[str, Any]] = None

# Query response
class QueryResponse(BaseModel):
    query: str
    db_schema: Dict[str, Any]
    guidance: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

# SQL result message
class SQLResultMessage(BaseModel):
    sql_query: str
    result: List[Dict[str, Any]]
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

# Excel request message
class ExcelRequestMessage(BaseModel):
    query: str
    sql_query: str
    result: List[Dict[str, Any]]
    format_options: Optional[Dict[str, Any]] = None

# Agent State - (Using in LangChain)
class AgentState(BaseModel):
    user_query: str
    current_agent: str
    db_schema: Optional[Dict[str, Any]] = None
    sql_query: Optional[str] = None
    query_result: Optional[List[Dict[str, Any]]] = None
    excel_path: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}
    messages: List[AgentMessage] = []