FROM python:3.10-slim

WORKDIR /workspace

# Install curl for healthchecks
RUN apt-get update \
 && apt-get install -y curl \
 && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir sse-starlette jwcrypto

COPY . .

# Expose port
EXPOSE 10001

# Start uvicorn via the FastAPI app you exported in __main__.py
CMD ["uvicorn", "app.agents.database_agent.__main__:app", "--host", "0.0.0.0", "--port", "10001"]
