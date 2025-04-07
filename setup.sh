#!/bin/bash

# Booner MCP Setup Script
# This script sets up the necessary dependencies and initializes the MCP environment

echo "Setting up Booner MCP..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
mkdir -p servers

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
npm install -g n
n 18.16.0

# Install base MCP servers using NPX
echo "Installing MCP servers..."
npx -y @modelcontextprotocol/server-filesystem
npx -y @modelcontextprotocol/server-git
npx -y @modelcontextprotocol/server-time
npx -y @modelcontextprotocol/server-memory

# Setup Ollama and pull required models
echo "Setting up Ollama..."
docker pull ollama/ollama:latest

echo "Pulling Mixtral model from Ollama..."
docker run --rm ollama/ollama pull mixtral

# Setup Python virtual environment
echo "Setting up Python virtual environment..."
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Initialize configuration
echo "Initializing configuration..."
# Update the mcp_config.json file with appropriate paths
sed -i 's|/path/to/allowed/files|'$(pwd)'/data|g' config/mcp_config.json

echo "Setup complete!"
echo "To start the services, run: docker-compose up -d"
echo "To access the API documentation, visit: http://localhost:8000/docs"
