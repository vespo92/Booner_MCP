# Booner MCP WebSocket Integration

This guide explains how to use the new WebSocket functionality in the Booner MCP API.

## Overview

WebSockets provide real-time updates without the need for polling. Two WebSocket endpoints have been added:

1. `/ws/system/status` - Real-time system status updates
2. `/ws/tasks/updates` - Real-time task status updates

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. To use the WebSocket-enabled version of the API, run:

```bash
python app_with_websockets.py
```

## Using WebSockets in the Frontend

The frontend hooks in `booner-mcp-web` have already been updated to use these WebSocket endpoints. The `useSystemStatus` hook will automatically:

1. First try to establish a WebSocket connection
2. If WebSocket connection fails, it will fall back to traditional REST API polling
3. Receive real-time updates when available

## WebSocket Endpoints

### System Status Updates

Connect to: `ws://localhost:8000/ws/system/status`

This WebSocket provides real-time system status updates, including:
- Main server status (CPU, memory, disk)
- Deployment target status

Example received data:
```json
{
  "main_server": {
    "cpu": "Intel(R) Core(TM) i7-10700K (8 cores @ 3.80 GHz, 22% used)",
    "gpu": "NVIDIA GeForce RTX 3080 (8GB/10GB @ 65°C)",
    "ram": "32.00 GB (45% used)",
    "disk": "512.00 GB (68% used)",
    "status": "active"
  },
  "deployment_targets": [
    {
      "host": "10.0.0.2",
      "status": "active",
      "load": 0.3,
      "specs": "Standard deployment target"
    }
  ]
}
```

### Task Status Updates

Connect to: `ws://localhost:8000/ws/tasks/updates`

This WebSocket provides real-time updates on all tasks in the system, including:
- Task creation
- Status changes
- Completion or failure events

Example received data:
```json
{
  "task-uuid-1": {
    "status": "running"
  },
  "task-uuid-2": {
    "status": "completed",
    "result": { "details": "Task completed successfully" }
  },
  "task-uuid-3": {
    "status": "failed",
    "error": "Failed to deploy: Connection refused"
  }
}
```

## Implementation Details

- The WebSocket server automatically broadcasts system status every 3 seconds to active connections
- Task updates are broadcasted immediately whenever a task status changes
- Both WebSocket endpoints have fallback REST API endpoints for compatibility

## Testing WebSocket Connections

You can test WebSocket connections using tools like [websocat](https://github.com/vi/websocat):

```bash
# Install websocat
cargo install websocat

# Connect to system status WebSocket
websocat ws://localhost:8000/ws/system/status
```

## Troubleshooting

If you experience issues with WebSockets:

1. Check that ports 8000 is open and accessible
2. Verify that your firewall allows WebSocket connections
3. Check browser console for any WebSocket connection errors
4. The system will automatically fall back to REST API polling if WebSockets fail
