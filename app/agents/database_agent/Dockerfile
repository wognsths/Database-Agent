# Dockerfile for building Database Agent
FROM python:3.10-slim

WORKDIR /workspace

# Install basic dependencies
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies
RUN pip install --no-cache-dir sse-starlette jwcrypto 

# Copy application code
COPY . .

# Run Database Agent
CMD ["python", "-m", "app.agents.database_agent", "--host", "0.0.0.0", "--port", "10001"] 