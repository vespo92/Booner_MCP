# Booner MCP Server Configuration

This directory contains configuration files and templates for the managed servers in the Booner MCP ecosystem.

## Server Overview

| Machine | Role | IP | Hardware | Status |
|---------|------|----|---------| ------ |
| Machine 1 | Booner_Ollama (LLM Server) | 10.0.0.1 | Ryzen 7 5700x3d, 64GB RAM, 1TB NVMe, RTX 4070 Ti Super | Planned |
| Machine 2 | Booner_MCP & booner-mcp-web | 10.0.0.4 | Ryzen 9 3900x, 64GB RAM, 1TB NVMe, Quadro P4000 | In Progress |
| Machine 3 | OPN_IaC | 10.0.0.2 | Xeon E5-2680v4, 16GB RAM, RTX 3050 8GB | Planned |
| Machine 4 | Worker Node | 10.0.200.21 | Ryzen 5 3600, 32GB RAM, 512GB NVMe | Planned |
| Machine 5 | Worker Node | 10.0.201.17 | Ryzen 7 5700x3d, 32GB RAM, 250GB SSD | Planned |

## Directory Structure

- `/servers` - Main directory for server configurations
  - `/templates` - Deployment templates for different server types
  - `/configs` - Configuration files for active servers
  - `/inventory` - Server inventory and tracking
  - `/access` - SSH and authentication configurations (encrypted)
  - `/state` - Deployment state tracking (managed by MCP)

## Implementation Approach

### Authentication & Access

For secure access between machines, we recommend:

1. SSH Key-based authentication
2. Creation of dedicated service accounts on each machine
3. Restricted sudo access for automated operations
4. Network-level access controls between machines

### Deployment Workflow

Server deployments should follow this workflow:

1. Template selection through Booner_MCP web interface
2. Parameter configuration for the specific deployment
3. Task creation by MCP
4. Handoff to OPN_IaC for provisioning
5. State maintenance and monitoring post-deployment

### Configuration Management

All server configurations should be maintained as code and stored in this directory structure. 
Dynamic configurations should be tracked in the MCP database with version history.

## Next Steps

1. Complete the server templates directory with Pulumi configurations
2. Set up SSH key distribution
3. Implement secure credential management
4. Create deployment workflows for each server type