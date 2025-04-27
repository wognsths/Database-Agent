from fastapi import FastAPI, HTTPException, Depends, Request, Body
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from app.agents.host.multiagent.host_agent import HostAgent  # Import host_agent class directly
from app.core.config import settings
import json
import asyncio
import logging
import uuid

# Logging settings
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add detailed logging
logger.info("Starting API module initialization")
logger.info("Attempting to connect to database agent (http://db-agent-database-agent:10001)...")

# Create HostAgent instance directly instead of ADK agent
try:
    host_agent = HostAgent([settings.DATABASE_AGENT_URL])
    logger.info(f"HostAgent initialization complete. Connected agents: {host_agent.list_remote_agents()}")
except Exception as e:
    logger.error(f"Error during HostAgent initialization: {str(e)}")
    # Initialize with empty agent list so server can start even if an error occurs
    host_agent = HostAgent([])

app = FastAPI(
    title="Host Agent API",
    description="API for the Host Agent", 
    version="1.0.0"
)

@app.get("/", response_class=HTMLResponse)
async def root():
    # Provide simple management page HTML
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Host Agent Management</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1 { color: #333; }
            .container { max-width: 800px; margin: 0 auto; }
            .card { border: 1px solid #ddd; padding: 16px; margin-bottom: 20px; border-radius: 4px; }
            .form-group { margin-bottom: 15px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input[type="text"] { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
            button { background-color: #4CAF50; color: white; padding: 10px 15px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background-color: #45a049; }
            #message { padding: 10px; margin-top: 10px; border-radius: 4px; display: none; }
            .success { background-color: #d4edda; color: #155724; }
            .error { background-color: #f8d7da; color: #721c24; }
            #agentList { margin-top: 20px; }
            table { width: 100%; border-collapse: collapse; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Host Agent Management</h1>
            
            <div class="card">
                <h2>Agent Registration</h2>
                <div class="form-group">
                    <label for="agentUrl">Agent URL:</label>
                    <input type="text" id="agentUrl" placeholder="http://database_agent:10001">
                </div>
                <button onclick="registerAgent()">Register</button>
                <div id="message"></div>
            </div>
            
            <div class="card">
                <h2>Registered Agent List</h2>
                <button onclick="loadAgents()">Refresh</button>
                <div id="agentList">
                    <p>Loading agent list...</p>
                </div>
            </div>
        </div>
        
        <script>
            // Load agent list when page loads
            window.onload = function() {
                loadAgents();
            };
            
            // Agent registration function
            async function registerAgent() {
                const agentUrl = document.getElementById('agentUrl').value.trim();
                if (!agentUrl) {
                    showMessage('Please enter an agent URL.', 'error');
                    return;
                }
                
                try {
                    const response = await fetch('/register_agent', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ agent_url: agentUrl })
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok) {
                        showMessage(`Agent '${data.agent_name}' has been successfully registered.`, 'success');
                        loadAgents();
                    } else {
                        showMessage(`Error: ${data.detail || 'An unknown error occurred.'}`, 'error');
                    }
                } catch (error) {
                    showMessage(`Request failed: ${error.message}`, 'error');
                }
            }
            
            // Load agent list function
            async function loadAgents() {
                try {
                    const response = await fetch('/agents');
                    const agents = await response.json();
                    
                    const agentListDiv = document.getElementById('agentList');
                    
                    if (agents.length === 0) {
                        agentListDiv.innerHTML = '<p>No registered agents found.</p>';
                        return;
                    }
                    
                    let tableHtml = `
                        <table>
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Description</th>
                                </tr>
                            </thead>
                            <tbody>
                    `;
                    
                    agents.forEach(agent => {
                        tableHtml += `
                            <tr>
                                <td>${agent.name}</td>
                                <td>${agent.description}</td>
                            </tr>
                        `;
                    });
                    
                    tableHtml += `
                            </tbody>
                        </table>
                    `;
                    
                    agentListDiv.innerHTML = tableHtml;
                } catch (error) {
                    document.getElementById('agentList').innerHTML = `<p>An error occurred while loading the agent list: ${error.message}</p>`;
                }
            }
            
            // Display message function
            function showMessage(message, type) {
                const messageDiv = document.getElementById('message');
                messageDiv.textContent = message;
                messageDiv.className = type;
                messageDiv.style.display = 'block';
                
                // Hide message after 5 seconds
                setTimeout(() => {
                    messageDiv.style.display = 'none';
                }, 5000);
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# Agent card endpoint
@app.get("/agent")
async def get_agent_card():
    agent_info = {
        "name": "Host Agent",
        "description": "Agent that can delegate tasks to other agents",
        "capabilities": {
            "streaming": True
        }
    }
    return JSONResponse(content=agent_info)

# Retrieve remote agent list
@app.get("/agents")
async def list_agents():
    agents = host_agent.list_remote_agents()
    logger.info(f"Agent list request. Response: {agents}")
    return JSONResponse(content=agents)

# Add endpoint for manual remote agent registration
@app.post("/register_agent")
async def register_agent(agent_url: str = Body(..., embed=True)):
    try:
        logger.info(f"Attempting manual agent registration: {agent_url}")
        from app.common.client import A2ACardResolver
        card_resolver = A2ACardResolver(agent_url)
        card = card_resolver.get_agent_card()
        host_agent.register_agent_card(card)
        logger.info(f"Successfully registered agent '{card.name}'")
        return {"success": True, "agent_name": card.name}
    except Exception as e:
        logger.error(f"Agent registration failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Agent registration failed: {str(e)}")

# Task sending process
@app.post("/task")
async def send_task(request_data: dict = Body(...)):
    try:
        agent_name = request_data.get("agent_name")
        message = request_data.get("message")
        
        if not agent_name or not message:
            raise HTTPException(status_code=400, detail="Missing agent_name or message")
            
        # Use custom context object instead of standard ToolContext
        class CustomToolContext:
            def __init__(self):
                self.state = {}
                self.actions = type('Actions', (), {'skip_summarization': False, 'escalate': False})
                
            def save_artifact(self, file_id, file_part):
                # Implement artifact saving (if needed)
                pass
        
        tool_context = CustomToolContext()
        
        # Asynchronous function call
        logger.info(f"Sending task: agent={agent_name}, message={message[:50]}...")
        response = await host_agent.send_task(agent_name, message, tool_context)
        return JSONResponse(content={"result": response})
    except Exception as e:
        logger.error(f"Task sending failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

# Add debugging endpoint for direct database agent communication
@app.post("/debug_db_agent")
async def debug_db_agent(request_data: dict = Body(...)):
    try:
        message = request_data.get("message", "Get db schema by using database agent")
        logger.info(f"Debug endpoint called with message: {message}")
        
        # Create a custom tool context
        class CustomToolContext:
            def __init__(self):
                self.state = {
                    "session_id": str(uuid.uuid4()),
                    "input_message_metadata": {"message_id": str(uuid.uuid4())}
                }
                self.actions = type('Actions', (), {'skip_summarization': False, 'escalate': False})
                
            def save_artifact(self, file_id, file_part):
                # Implement artifact saving (if needed)
                pass
        
        tool_context = CustomToolContext()
        
        # Make direct call to database agent
        logger.info("Sending direct request to Database Agent...")
        response = await host_agent.send_task("Database Agent", message, tool_context)
        
        # Log the response extensively
        logger.info(f"Response from Database Agent: {response}")
        
        return JSONResponse(content={"result": response})
    except Exception as e:
        logger.error(f"Debug endpoint error: {str(e)}")
        logger.exception("Full exception traceback:")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        ) 