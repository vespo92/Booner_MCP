# Server State Directory

This directory is managed by the MCP system and contains the current state of all deployed servers.

**Do not manually edit files in this directory.**

The state files are automatically generated and updated by the MCP system during deployment operations.

## Contents

- `*.tfstate` - Terraform state files
- `*.json` - Pulumi state files
- `summary.yaml` - Human-readable summary of all deployments
- `<server_name>/` - Directories containing server-specific state information

## Usage

The state information can be accessed through the MCP API or web interface.
