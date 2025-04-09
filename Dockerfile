FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    wget \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js dependencies
RUN npm install -g n
RUN n 18.16.0

# Install Python dependencies for MCP servers
RUN pip install --no-cache-dir uv
RUN pip install --no-cache-dir uvx

# Copy configuration files
COPY ./config /app/config/

# Copy agent code
COPY ./agents /app/agents/

# Copy API code
COPY ./api /app/api/

# Copy servers directory
COPY ./servers /app/servers/

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Install MCP servers - can uncomment if needed
# RUN npx -y @modelcontextprotocol/server-filesystem
# RUN npx -y @modelcontextprotocol/server-git
# RUN npx -y @modelcontextprotocol/server-time
# RUN npx -y @modelcontextprotocol/server-memory

# Make sure Python can find the modules
ENV PYTHONPATH=/app:$PYTHONPATH

# Expose API port
EXPOSE 8000

# Command to run the API with WebSocket support
CMD ["uvicorn", "api.app_with_websockets:app", "--host", "0.0.0.0", "--port", "8000"]
