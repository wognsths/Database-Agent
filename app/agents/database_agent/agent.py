from typing import Any, Dict, List, Optional, Literal, AsyncIterable
from pydantic import BaseModel
import httpx

from langchain_google_genai import ChatGoogleGenerativeAI

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, ToolMessage

from app.core.config import settings
from app.core.database import db, schema_manager
from app.core.models import QueryRequest, QueryResponse, SQLResultMessage
from app.agents.database_agent.tools import get_database_schema, get_table_list, get_table_sample, run_custom_query

memory = MemorySaver()

class DBAgentResponse(BaseModel):
    """Respond to the user in this format."""
    status: Literal["input_required", "completed", "error"] = "input_required"
    message: str

class DBAgent:
    SYSTEM_INSTRUCTION = (
        "You are a database assistant specialized in interacting with relational databases. "
        "You can use the following tools to fulfill user requests:\n\n"
        "- get_database_schema: Retrieve the overall database schema, including tables and their columns.\n"
        "- get_table_list: Retrieve a list of all available tables in the database.\n"
        "- get_table_sample: Fetch a small sample of rows from a specific table (default limit is 5 rows).\n"
        "- run_custom_query: Execute a custom SQL query provided by the user and return the results.\n\n"
        "Use these tools appropriately based on the user's intent. "
        "You must not attempt to answer questions beyond the scope of database exploration and query execution. "
        "If you need more information from the user to proceed, set the response status to 'input_required'. "
        "If an error occurs while using a tool, set the response status to 'error'. "
        "If the task is successfully completed, set the response status to 'completed'. "
        "Respond concisely and accurately based on the tool outputs."
    )
    def __init__(self):
        self.model = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
        self.tools = [
            get_database_schema,
            get_table_list,
            get_table_sample,
            run_custom_query
        ]
        self.graph = create_react_agent(
            self.model, tools=self.tools, checkpointer=memory, prompt = self.SYSTEM_INSTRUCTION, response_format=DBAgentResponse
        )
    def invoke(self, query, sessionId) -> DBAgentResponse:
        config = {"configurable": {"thread_id": sessionId}}
        self.graph.invoke({"messages": [("user", query)]}, config)        
        return self.get_agent_response(config)
    
    async def stream(self, query, sessionId) -> AsyncIterable[Dict[str, Any]]:
        inputs = {"messages": [("user", query)]}
        config = {"configurable": {"thread_id": sessionId}}

        for item in self.graph.stream(inputs, config, stream_mode="values"):
            message = item["messages"][-1]
            if (
                isinstance(message, AIMessage)
                and message.tool_calls
                and len(message.tool_calls) > 0
            ):
                yield {
                    "is_task_complete": False,
                    "require_user_input": False,
                    "content": "Analyzing database schema and processing query...",
                }
            elif isinstance(message, ToolMessage):
                yield {
                    "is_task_complete": False,
                    "require_user_input": False,
                    "content": "Executing SQL query and formatting results...",
                }            
        
        yield self.get_agent_response(config)


    def get_agent_response(self, config):
        current_state = self.graph.get_state(config)        
        structured_response = current_state.values.get('structured_response')
        if structured_response and isinstance(structured_response, DBAgentResponse): 
            if structured_response.status == "input_required":
                return {
                    "is_task_complete": False,
                    "require_user_input": True,
                    "content": structured_response.content
                }
            elif structured_response.status == "error":
                return {
                    "is_task_complete": False,
                    "require_user_input": True,
                    "content": structured_response.content
                }
            elif structured_response.status == "completed":
                return {
                    "is_task_complete": True,
                    "require_user_input": False,
                    "content": structured_response.content
                }

        return {
            "is_task_complete": False,
            "require_user_input": True,
            "content": "We are unable to process your request at the moment. Please try again.",
        }

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]
