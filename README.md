# Booner_MCP

An AI infrastructure-as-code platform using Model Context Protocol (MCP) with Ollama for agentic coding and server management.

## Overview

This project allows AI agents to interact with local infrastructure, deploy and manage various server types (web servers, game servers, databases) through the Model Context Protocol. It integrates with a local Ollama deployment running mixtral on powerful hardware.

## System Architecture

### Machines Configuration

- **Machine 1 (Booner_Ollama - 10.0.0.10)**:
  - Runs Ollama LLM server on port 11434
  - Provides AI capabilities to the MCP system
  - Hardware: AMD 5700X3D, 4070 Ti Super, 64GB RAM, Quadro P4000

- **Machine 2 (Booner_MCP & agent - 10.0.0.4)**:
  - Runs the MCP core management API
  - Runs the Next.js web interface
  - Hardware: Ryzen 7 5700X3D, 32GB RAM
  - Worker Agent for Agentic Coding

- **Machine 3 (booner-mcp-web & agent - 10.0.0.4)**:
  - Runs the Web GUI to interact with MCP & Ollama
  - Worker Agent for Agentic Coding

- **Machine 3 (OPN_IaC - 10.0.0.2)**:
  - Runs infrastructure as code tools
  - Dedicated OPNSense Network API

- **Deployment Targets (Machine N)**:
  - Run game servers, web applications, etc.
  - Hardware examples:
  - E5-2680 v4, 16GB RAM, RTX 3050 8GB

- **Storage**: TrueNAS with 8TB HDD & 2TB SSD (NFS shared)

### Software Stack

- **OS**: Ubuntu 24 (all machines)
- **LLM**: Mixtral via Ollama
- **Primary Languages**: Python, Go, NextJS
- **Containerization**: Docker

## Project Structure

- `agents/`: AI agent definitions and orchestration code
- `servers/`: MCP server implementations for different infrastructure tasks
- `api/`: API server for agent communication
- `config/`: Configuration files for different environments and systems

## Setup & Deployment

### Prerequisites

- Git with support for submodules
- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### Initial Setup

1. Clone the repository with submodules:
   ```bash
   git clone --recurse-submodules https://github.com/vespo92/Booner_MCP.git
   cd Booner_MCP
   ```

2. Create an environment file:
   ```bash
   cp .env.example .env
   ```

3. Generate a secure AUTH_SECRET:
   ```bash
   # On Linux/macOS
   ./generate_auth_secret.sh
   
   # On Windows
   .\generate_auth_secret.ps1
   ```

4. Deploy with Docker Compose:
   ```bash
   docker-compose up -d
   ```

### Accessing the Services

- **Web UI**: http://10.0.0.1:3000
- **API**: http://10.0.0.1:8000
- **Ollama**: http://10.0.0.10:11434

## Development Workflow

### Working with the Main Project

```bash
cd Booner_MCP
# Make changes
git add .
git commit -m "Your commit message"
git push origin main
```
