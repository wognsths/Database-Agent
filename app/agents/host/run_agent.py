import uvicorn
import time

if __name__ == "__main__":
    print("Waiting for database_agent to start...")
    time.sleep(10)
    
    uvicorn.run(
        "app.agents.host.multiagent.api:app",
        host="0.0.0.0",
        port=10000,
        reload=False
    )
