from typing import Callable
import uuid
from app.common.types import (
    AgentCard,
    Task,
    TaskSendParams,
    TaskStatusUpdateEvent,
    TaskArtifactUpdateEvent,
    TaskStatus,
    TaskState
)
from app.common.client import A2AClient

TaskCallbackArg = Task | TaskStatusUpdateEvent | TaskArtifactUpdateEvent
TaskUpdateCallback = Callable[[TaskCallbackArg, AgentCard], Task]

class RemoteAgentConnections:
    """A class to hold the connections to the remote agents."""

    def __init__(self, agent_card: AgentCard):
        self.agent_client = A2AClient(agent_card)
        self.card = agent_card

        self.conversation_name = None
        self.conversation = None
        self.pending_tasks = set()

    def get_agent(self) -> AgentCard:
        return self.card
    
    async def send_task(
            self,
            request: TaskSendParams,
            task_callback: TaskUpdateCallback | None,
    ) -> Task | None:
        print(f"RemoteAgentConnections.send_task - Request: {request.model_dump()}")
        print(f"Using A2AClient with URL: {self.agent_client.url}")
        
        if self.card.capabilities.streaming:
            print(f"Using streaming capabilities for agent: {self.card.name}")
            task = None
            if task_callback:
                initial_task = Task(
                    id=request.id,
                    sessionId=request.sessionId,
                    status=TaskStatus(
                        state=TaskState.SUBMITTED,
                        message=request.message,
                    ),
                    history=[request.message],
                )
                print(f"Calling task_callback with initial task: {initial_task}")
                task_callback(initial_task, self.card)
            
            async for response in self.agent_client.send_task_streaming(request.model_dump()):
                print(f"Received streaming response: {response}")
                merge_metadata(response.result, request)
                # For task status updates, we need to propagate metadata and provide
                # a unique message id.
                if (hasattr(response.result, 'status') and
                    hasattr(response.result.status, 'merge') and
                    response.result.status.message):
                    merge_metadata(response.result.status.message, request.message)
                    m = response.result.status.message
                    if not m.metadata:
                        m.metadata = {}
                    if 'message_id' in m.metadata:
                        m.metadata['last_message_id'] = m.metadata['message_id']
                    m.metadata['message_id'] = str(uuid.uuid4())
                
                if task_callback:
                    print(f"Calling task_callback with response: {response.result}")
                    task = task_callback(response.result, self.card)
                
                if hasattr(response.result, 'final') and response.result.final:
                    print("Final response received, breaking loop")
                    break
            
            print(f"Streaming request complete, returning task: {task}")
            return task
        else:
            print(f"Using non-streaming API for agent: {self.card.name}")
            response = await self.agent_client.send_task(request.model_dump())
            print(f"Received non-streaming response: {response}")
            merge_metadata(response.result, request)
            # For task status updates, we need to propagate metadata and provide
            # a unique message id.
            if (hasattr(response.result, 'status') and
                hasattr(response.result.status, 'message') and
                response.result.status.message):
                merge_metadata(response.result.status.message, request.message)
                m = response.result.status.message
                if not m.metadata:
                    m.metadata = {}
                if 'message_id' in m.metadata:
                    m.metadata['last_message_id'] = m.metadata['message_id']
                m.metadata['message_id'] = str(uuid.uuid4())
            
            if task_callback:
                print(f"Calling task_callback with response: {response.result}")
                task_callback(response.result, self.card)
            
            print(f"Non-streaming request complete, returning: {response.result}")
            return response.result

def merge_metadata(target, source):
    if not hasattr(target, 'metadata') or not hasattr(source, 'metadata'):
        return
    if target.metadata and source.metadata:
        target.metadata.update(source.metadata)
    elif source.metadata:
        target.metadata = dict(**source.metadata)
