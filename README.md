# Booner_MCP

An AI infrastructure-as-code platform using Model Context Protocol (MCP) with Ollama for agentic coding and server management.

## Overview

This project allows AI agents to interact with local infrastructure, deploy and manage various server types (web servers, game servers, databases) through the Model Context Protocol. It integrates with a local Ollama deployment running mixtral on powerful hardware.

## System Architecture

- **Hardware**:
  - Main MCP Server: AMD 5700X3D, 4070 Ti Super, 64GB RAM, Quadro P4000
  - Deployment Targets:
    - Ryzen 5 3600, 32GB RAM
    - E5-2680 v4, 16GB RAM, RTX 3050 8GB
    - Ryzen 7 5700X3D, 32GB RAM
  - Storage: TrueNAS with 8TB HDD & 2TB SSD (NFS shared)

- **Software**:
  - OS: Ubuntu 24 (all machines)
  - LLM: Mixtral via Ollama
  - Primary Languages: Python, Go, NextJS

## Components

- `agents/`: AI agent definitions and orchestration code
- `servers/`: MCP server implementations for different infrastructure tasks
- `api/`: API server for agent communication
- `config/`: Configuration files for different environments and systems

## Getting Started

[Instructions to be added]

## License

[License to be added]
