from .host_agent import HostAgent

# Remove self-reference and only keep database_agent
# When Docker container starts, host_agent itself is not yet running, which causes connection errors
root_agent = HostAgent([
    "http://database_agent:10001" # Use Docker service name (only valid within Docker network)
]).create_agent()