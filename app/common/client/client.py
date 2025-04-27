import httpx
from httpx_sse import connect_sse
from typing import Any, AsyncIterable
from app.common.types import (
    AgentCard,
    GetTaskRequest,
    SendTaskRequest,
    SendTaskResponse,
    JSONRPCRequest,
    GetTaskResponse,
    CancelTaskResponse,
    CancelTaskRequest,
    SetTaskPushNotificationRequest,
    SetTaskPushNotificationResponse,
    GetTaskPushNotificationRequest,
    GetTaskPushNotificationResponse,
    A2AClientHTTPError,
    A2AClientJSONError,
    SendTaskStreamingRequest,
    SendTaskStreamingResponse,
)
import json


class A2AClient:
    def __init__(self, agent_card: AgentCard = None, url: str = None):
        if agent_card:
            self.url = agent_card.url
        elif url:
            self.url = url
        else:
            raise ValueError("Must provide either agent_card or url")
            
        # URL이 /로 끝나는지 확인하고, 아니면 /를 추가합니다
        if not self.url.endswith('/'):
            self.url = self.url + '/'
            
        # '/send-task'로 보내지 않도록 로깅 추가
        print(f"A2AClient initialized with URL: {self.url}")

    async def send_task(self, payload: dict[str, Any]) -> SendTaskResponse:
        request = SendTaskRequest(params=payload)
        return SendTaskResponse(**await self._send_request(request))

    async def send_task_streaming(
        self, payload: dict[str, Any]
    ) -> AsyncIterable[SendTaskStreamingResponse]:
        request = SendTaskStreamingRequest(params=payload)
        request_data = request.model_dump()
        print(f"Sending streaming request to {self.url}: {request_data}")
        
        with httpx.Client(timeout=None) as client:
            try:
                print(f"Opening SSE connection to {self.url}")
                with connect_sse(
                    client, "POST", self.url, json=request_data
                ) as event_source:
                    try:
                        for sse in event_source.iter_sse():
                            print(f"Received SSE event: {sse.data[:100]}...")
                            response = SendTaskStreamingResponse(**json.loads(sse.data))
                            yield response
                    except json.JSONDecodeError as e:
                        error_msg = f"JSON decode error in streaming: {str(e)}"
                        print(error_msg)
                        raise A2AClientJSONError(error_msg) from e
                    except Exception as e:
                        error_msg = f"Streaming error: {str(e)}"
                        print(error_msg)
                        raise
            except httpx.RequestError as e:
                error_msg = f"HTTP request error in streaming: {str(e)}"
                print(error_msg)
                raise A2AClientHTTPError(400, error_msg) from e

    async def _send_request(self, request: JSONRPCRequest) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            try:
                # 요청 정보 로깅
                request_data = request.model_dump()
                print(f"Sending request to {self.url}: {request_data}")
                
                # Image generation could take time, adding timeout
                response = await client.post(
                    self.url, json=request_data, timeout=30
                )
                response.raise_for_status()
                
                # 응답 정보 로깅
                response_data = response.json()
                print(f"Received response: {response_data}")
                
                return response_data
            except httpx.HTTPStatusError as e:
                error_msg = f"HTTP error: {e.response.status_code} - {e.response.text}"
                print(error_msg)
                raise A2AClientHTTPError(e.response.status_code, error_msg) from e
            except json.JSONDecodeError as e:
                error_msg = f"JSON decode error: {str(e)}"
                print(error_msg)
                raise A2AClientJSONError(error_msg) from e
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                print(error_msg)
                raise

    async def get_task(self, payload: dict[str, Any]) -> GetTaskResponse:
        request = GetTaskRequest(params=payload)
        return GetTaskResponse(**await self._send_request(request))

    async def cancel_task(self, payload: dict[str, Any]) -> CancelTaskResponse:
        request = CancelTaskRequest(params=payload)
        return CancelTaskResponse(**await self._send_request(request))

    async def set_task_callback(
        self, payload: dict[str, Any]
    ) -> SetTaskPushNotificationResponse:
        request = SetTaskPushNotificationRequest(params=payload)
        return SetTaskPushNotificationResponse(**await self._send_request(request))

    async def get_task_callback(
        self, payload: dict[str, Any]
    ) -> GetTaskPushNotificationResponse:
        request = GetTaskPushNotificationRequest(params=payload)
        return GetTaskPushNotificationResponse(**await self._send_request(request))
