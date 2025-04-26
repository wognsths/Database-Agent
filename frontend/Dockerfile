FROM python:3.10-slim

WORKDIR /workspace

# Install required system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY frontend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code to maintain project structure
COPY frontend/ /workspace/frontend/
COPY app/common/ /workspace/app/common/
COPY app/agents/ /workspace/app/agents/

# Set Python module path
ENV PYTHONPATH=/workspace

# Expose the application port
EXPOSE 12000

# Define the startup command
CMD ["python", "frontend/ui/main.py"]
