# Dockerfile for building Host Agent
FROM python:3.10-slim

WORKDIR /workspace

# Install basic dependencies
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies
RUN pip install --no-cache-dir google-adk

# Copy application code
COPY . .

# Run Host Agent
CMD ["python", "-m", "app.agents.host.run_agent"] 