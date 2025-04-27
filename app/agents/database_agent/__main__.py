import os
import logging
from dotenv import load_dotenv

from starlette.responses import JSONResponse
from app.common.server import A2AServer
from app.common.types import AgentCard, AgentCapabilities, AgentSkill, MissingAPIKeyError
from app.common.utils.push_notification_auth import PushNotificationSenderAuth
from app.agents.database_agent.task_manager import AgentTaskManager
from app.agents.database_agent.agent import DBAgent

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize push notification sender (if needed)
notification_sender_auth = PushNotificationSenderAuth()
notification_sender_auth.generate_jwk()

# Define agent capabilities and skills
capabilities = AgentCapabilities(streaming=True, pushNotifications=True)
skill = AgentSkill(
    id="text_to_sql",
    name="Text to SQL",
    description="Helps with converting natural language queries into SQL queries and access the database.",
    tags=["text-to-sql", "database management"],
    examples=["I want to get data related to electric machines from the database"]
)

# Define agent card
agent_card = AgentCard(
    name="Database Agent",
    description="Agent specialized in handling SQL queries based on natural language inputs.",
    url="http://db-agent-database-agent:10001/",
    version="1.0.0",
    defaultInputModes=DBAgent.SUPPORTED_CONTENT_TYPES,
    defaultOutputModes=DBAgent.SUPPORTED_CONTENT_TYPES,
    capabilities=capabilities,
    skills=[skill],
)

# Create the A2A server
server = A2AServer(
    agent_card=agent_card,
    task_manager=AgentTaskManager(
        agent=DBAgent(),
        notification_sender_auth=notification_sender_auth,
    ),
    host="0.0.0.0",
    port=10001,
)

# Expose Starlette app instance for uvicorn
app = server.app

# Health check endpoint (using Starlette route since app is a Starlette instance)
@app.route("/health", methods=["GET"])
async def health_check(request):
    return JSONResponse({"status": "ok"})
