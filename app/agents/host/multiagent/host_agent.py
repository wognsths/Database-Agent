import sys
import asyncio
import functools
import json
import uuid
import threading
import time
import httpx
import logging
from typing import List, Optional, Callable

# Logging settings
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from google.genai import types
import base64

from google.adk import Agent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.tool_context import ToolContext
from .remote_agent_connection import (
    RemoteAgentConnections,
    TaskUpdateCallback
)
from app.common.client import A2ACardResolver
from app.common.types import (
    AgentCard,
    Message,
    TaskState,
    Task,
    TaskSendParams,
    TextPart,
    DataPart,
    Part,
    TaskStatusUpdateEvent,
)

class HostAgent:
    """
    The host agent

    This is the agent responsible for choosing which remote agents to send
    tasks to and coordinate their work
    """

    def __init__(
        self,
        remote_agent_addresses: List[str],
        task_callback: TaskUpdateCallback | None = None
    ):
        logger.info(f"Starting HostAgent initialization. Agent addresses to connect: {remote_agent_addresses}")
        self.task_callback = task_callback
        self.remote_agent_connections: dict[str, RemoteAgentConnections] = {}
        self.cards: dict[str, AgentCard] = {}
        
        # Add retry logic for agent connections
        for address in remote_agent_addresses:
            max_retries = 5  # Increased retry count
            retry_delay = 3  # Decreased retry interval
            for retry in range(max_retries):
                try:
                    logger.info(f"Attempting to connect to agent: {address} (attempt: {retry+1}/{max_retries})")
                    # Set explicit timeout
                    card_resolver = A2ACardResolver(address)
                    # Print API endpoint information
                    card_url = card_resolver.base_url + "/" + card_resolver.agent_card_path
                    logger.info(f"Agent card URL: {card_url}")
                    
                    # Direct request to better capture connection timeout errors
                    client = httpx.Client(timeout=10.0)  # 10 second timeout
                    try:
                        logger.info(f"Sending GET request: {card_url}")
                        response = client.get(card_url)
                        logger.info(f"Response status code: {response.status_code}, content: {response.text[:100]}...")
                    except Exception as req_error:
                        logger.error(f"Direct HTTP request failed: {str(req_error)}")
                        raise
                    
                    # Normal agent card parsing and connection addition
                    card = card_resolver.get_agent_card()
                    logger.info(f"Agent card received: {card.name}")
                    remote_connection = RemoteAgentConnections(card)
                    self.remote_agent_connections[card.name] = remote_connection
                    self.cards[card.name] = card
                    logger.info(f"Successfully connected to agent '{card.name}'. Address: {address}")
                    break
                except (httpx.ConnectError, httpx.ReadTimeout) as e:
                    logger.error(f"Network error: Cannot connect to {address}: {str(e)}")
                    if retry < max_retries - 1:
                        logger.info(f"Retrying after {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    else:
                        logger.error(f"Connection failed after {max_retries} attempts. Skipping agent: {address}")
                except Exception as e:
                    logger.error(f"Agent connection exception: {str(e)}, type: {type(e)}")
                    if retry < max_retries - 1:
                        logger.info(f"Retrying after {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    else:
                        logger.error(f"Connection failed after {max_retries} attempts. Skipping agent: {address}")
        
        # Connected agent summary
        if not self.cards:
            logger.warning("No connected agents!")
        else:
            logger.info(f"Connected to a total of {len(self.cards)} agents: {list(self.cards.keys())}")
            
        agent_info = []
        for ra in self.list_remote_agents():
            agent_info.append(json.dumps(ra))
        self.agents = "\n".join(agent_info)
        logger.info("HostAgent initialization complete")

    def register_agent_card(self, card: AgentCard):
        remote_connection = RemoteAgentConnections(card)
        self.remote_agent_connections[card.name] = remote_connection
        self.cards[card.name] = card
        agent_info = []
        for ra in self.list_remote_agents():
            agent_info.append(json.dumps(ra))
        self.agents = '\n'.join(agent_info)

    def create_agent(self) -> Agent:
        return Agent(
            model="gemini-2.0-flash-001",
            name="host_agent",
            instruction=self.root_instruction,
            before_model_callback=self.before_model_callback,
            description=(
                "This agent orchestrates the decomposition of the user request into"
                " tasks that can be performed by the child agents."
            ),
            tools=[
                self.list_remote_agents,
                self.send_task,
            ],
        )
    
    def root_instruction(self, context: ReadonlyContext) -> str:
        current_agent = self.check_state(context)
        return f"""You are a expert delegator that can delegate the user request to the appropriate remote agents.

Discovery:
- You can use `list_remote_agents` to list the available remote agents you can use to delegage the task.

Execution:
- For actionable tasks, you can use `create_task` to assign tasks to remote agents to perform.
Be sure to include the remote agent name when you respond to the user.

You can use `check_pending_task_states` to check the states of the pending tasks.

Please rely on tools to address the request, don't make up the response. If you are not sure, please ask the user for more details.
Focus on the most recent parts of the conversation primarily.

If there is an active agent, send the request to that agent with the update task tool.

Agents:
{self.agents}

Current agent: {current_agent['active_agent']}
"""
    
    def check_state(self, context: ReadonlyContext):
        state = context.state
        if ('session_id' in state and
            'session_active' in state and
            state['session_active'] and
            'agent' in state):
            return {"active_agent": f'{state["agent"]}'}
        return {"active_agent": "None"}
    
    def before_model_callback(self, callback_context: CallbackContext, llm_request):
        state = callback_context.state
        if 'session_active' not in state or not state['session_active']:
            if 'session_id' not in state:
                state['session_id'] = str(uuid.uuid4())
            state['session_active'] = True

    def list_remote_agents(self):
        """List the available remote agents you can use to delegate the task."""
        if not self.remote_agent_connections:
            return []
        
        remote_agent_info = []
        for card in self.cards.values():
            remote_agent_info.append(
                {"name": card.name, "description": card.description}
            )
        return remote_agent_info
    
    async def send_task(
            self,
            agent_name: str,
            message: str,
            tool_context: ToolContext):
        """Sends a task either streaming (if supported) or non-streaming.

        This will send a message to the remote agent named agent_name.

        Args:
        agent_name: The name of the agent to send the task to.
        message: The message to send to the agent for the task.
        tool_context: The tool context this method runs in.

        Yields:
        A dictionary of JSON data.
        """
        if agent_name not in self.remote_agent_connections:
            raise ValueError(f"Agent {agent_name} not found")
        state = tool_context.state
        state['agent'] = agent_name
        card = self.cards[agent_name]
        client = self.remote_agent_connections[agent_name]
        if not client:
            raise ValueError(f"Client not available for {agent_name}")
        if 'task_id' in state:
            taskId = state['task_id']
        else:
            taskId = str(uuid.uuid4())
        sessionId = state['session_id']
        task: Task
        messageId = ""
        metadata = {}
        if 'input_message_metadata' in state:
            metadata.update(**state['input_message_metadata'])
            if 'message_id' in state['input_message_metadata']:
                messageId = state['input_message_metadata']['message_id']
        if not messageId:
            messageId = str(uuid.uuid4())
        metadata.update(**{'conversation_id': sessionId, 'message_id': messageId})
        request: TaskSendParams = TaskSendParams(
            id=taskId,
            sessionId=sessionId,
            message=Message(
                role="user",
                parts=[TextPart(text=message)],
                metadata=metadata,
            ),
            acceptedOutputModes=["text", "text/plain", "image/png"],
            # pushNotification=None,
            metadata={'conversation_id': sessionId},
        )
        task = await client.send_task(request, self.task_callback)
        # Assume completion unless a state returns that isn't complete
        state['session_active'] = task.status.state not in [
            TaskState.COMPLETED,
            TaskState.CANCELED,
            TaskState.FAILED,
            TaskState.UNKNOWN,
        ]
        if task.status.state == TaskState.INPUT_REQUIRED:
            # force user input back
            tool_context.actions.skip_summarization = True
            tool_context.actions.escalate = True
        elif task.status.state == TaskState.CANCELED:
            # Open question, should we return some info for cancellation instead
            raise ValueError(f"Agent {agent_name} task {task.id} is cancelled")
        elif task.status.state == TaskState.FAILED:
            # Raise error for failure
            raise ValueError(f"Agent {agent_name} task {task.id} failed")
        response = []
        if task.status.message:
            # Assume the info is in the task message.
            response.extend(convert_parts(task.status.message.parts, tool_context))
        if task.artifacts:
            for artifact in task.artifacts:
                response.extend(convert_parts(artifact.parts, tool_context))
        return response
    
def convert_parts(parts: list[Part], tool_context: ToolContext):
    rval = []
    for p in parts:
        rval.append(convert_part(p, tool_context))
    return rval
    
def convert_part(part: Part, tool_context: ToolContext):
    if part.type == "text":
        return part.text
    elif part.type == "data":
        return part.data
    elif part.type == "file":
        # Repackage A2A FilePart to google.genai Blob
        # Currently not considering plain text as files    
        file_id = part.file.name
        file_bytes = base64.b64decode(part.file.bytes)    
        file_part = types.Part(
        inline_data=types.Blob(
            mime_type=part.file.mimeType,
            data=file_bytes))
        tool_context.save_artifact(file_id, file_part)
        tool_context.actions.skip_summarization = True
        tool_context.actions.escalate = True
        return DataPart(data = {"artifact-file-id": file_id})
    return f"Unknown type: {p.type}"