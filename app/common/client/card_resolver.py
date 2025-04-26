import httpx
from app.common.types import (
    AgentCard,
    A2AClientJSONError,
)
import json
import logging

logger = logging.getLogger(__name__)

class A2ACardResolver:
    def __init__(self, base_url, agent_card_path="/.well-known/agent.json", timeout=10.0):
        self.base_url = base_url.rstrip("/")
        self.agent_card_path = agent_card_path.lstrip("/")
        self.timeout = timeout
        logger.info(f"A2ACardResolver initialized: base_url={self.base_url}, path={self.agent_card_path}")

    def get_agent_card(self) -> AgentCard:
        full_url = f"{self.base_url}/{self.agent_card_path}"
        logger.info(f"Agent card request: {full_url} (timeout: {self.timeout}s)")
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                logger.debug(f"Starting HTTP GET request: {full_url}")
                response = client.get(full_url)
                logger.info(f"HTTP response received: status_code={response.status_code}")
                
                response.raise_for_status()
                try:
                    card_json = response.json()
                    logger.debug(f"JSON response: {card_json}")
                    card = AgentCard(**card_json)
                    logger.info(f"Agent card loaded successfully: {card.name}")
                    return card
                except json.JSONDecodeError as e:
                    error_msg = f"JSON parsing error: {str(e)}, response content: {response.text[:200]}"
                    logger.error(error_msg)
                    raise A2AClientJSONError(error_msg) from e
        except httpx.ConnectError as e:
            error_msg = f"Connection error: Cannot connect to {full_url}: {str(e)}"
            logger.error(error_msg)
            raise
        except httpx.TimeoutException as e:
            error_msg = f"Timeout: {full_url} request timed out after {self.timeout}s: {str(e)}"
            logger.error(error_msg)
            raise
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error: {e.response.status_code} - {e.response.text[:200]}"
            logger.error(error_msg)
            raise
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}, type: {type(e)}"
            logger.error(error_msg)
            raise
