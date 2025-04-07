# Booner MCP Setup Script (Windows)
# This script sets up the necessary dependencies and initializes the MCP environment

Write-Host "Setting up Booner MCP..." -ForegroundColor Green

# Check if Docker is installed
try {
    docker --version | Out-Null
}
catch {
    Write-Host "Docker is not installed. Please install Docker Desktop for Windows first." -ForegroundColor Red
    exit 1
}

# Create necessary directories
if (-not (Test-Path -Path "servers")) {
    New-Item -ItemType Directory -Path "servers" | Out-Null
}

# Check for Node.js
try {
    node --version | Out-Null
}
catch {
    Write-Host "Node.js is not installed. Please install Node.js first." -ForegroundColor Red
    exit 1
}

# Install base MCP servers using NPX
Write-Host "Installing MCP servers..." -ForegroundColor Green
npx -y @modelcontextprotocol/server-filesystem
npx -y @modelcontextprotocol/server-git
npx -y @modelcontextprotocol/server-time
npx -y @modelcontextprotocol/server-memory

# Setup Ollama and pull required models
Write-Host "Setting up Ollama..." -ForegroundColor Green
docker pull ollama/ollama:latest

Write-Host "Pulling Mixtral model from Ollama..." -ForegroundColor Green
docker run --rm ollama/ollama pull mixtral

# Setup Python virtual environment
Write-Host "Setting up Python virtual environment..." -ForegroundColor Green
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Initialize configuration
Write-Host "Initializing configuration..." -ForegroundColor Green
# Update the mcp_config.json file with appropriate paths
$config = Get-Content -Path "config\mcp_config.json" -Raw
$config = $config -replace "/path/to/allowed/files", (Get-Location).Path + "\data"
Set-Content -Path "config\mcp_config.json" -Value $config

Write-Host "Setup complete!" -ForegroundColor Green
Write-Host "To start the services, run: docker-compose up -d" -ForegroundColor Cyan
Write-Host "To access the API documentation, visit: http://localhost:8000/docs" -ForegroundColor Cyan
