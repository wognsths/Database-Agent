from .host_agent import HostAgent
from app.core.config import settings

root_agent = HostAgent([
    settings.DATABASE_AGENT_URL
]).create_agent()