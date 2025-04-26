from fastapi import FastAPI
from app.api import sample, query, schema

app = FastAPI(
    title="Database Agent API",
    description="API for the Database Agent project",
    version="1.0.0"
)

# Include API routers
app.include_router(sample.router, prefix="/api", tags=["sample"])
app.include_router(query.router, prefix="/api", tags=["query"])
app.include_router(schema.router, prefix="/api", tags=["schema"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Database Agent API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 