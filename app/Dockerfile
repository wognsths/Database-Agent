FROM python:3.10-slim

WORKDIR /workspace

# Install required system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code to maintain project structure
COPY app/ /workspace/app/
COPY app/common/ /workspace/common/

# Set Python module path
ENV PYTHONPATH=/workspace

# Expose the application port
EXPOSE 8000

# Define the startup command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
