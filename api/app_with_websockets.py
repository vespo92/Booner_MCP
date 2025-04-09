import os
import sys
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
import uuid

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import agent classes
from agents.base_agent import InfrastructureAgent
from agents.game_server_agent import GameServerAgent
from agents.web_server_agent import WebServerAgent
from api.system_monitor import system_monitor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Agent instances
agents = {}
active_tasks = {}

# WebSocket connection managers
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

# Create connection managers for different types of updates
system_status_manager = ConnectionManager()
task_status_manager = ConnectionManager()

# Models for API requests and responses
class DeployGameServerRequest(BaseModel):
    game: str
    target_host: Optional[str] = None
    server_name: str = "default"
    custom_config: Optional[Dict[str, Any]] = None

class UpdateGameServerRequest(BaseModel):
    game: str
    target_host: Optional[str] = None
    server_name: str = "default"

class StartGameServerRequest(BaseModel):
    game: str
    target_host: Optional[str] = None
    server_name: str = "default"
    custom_start_params: Optional[str] = None

class StopGameServerRequest(BaseModel):
    game: str
    target_host: Optional[str] = None
    server_name: str = "default"

class BackupGameServerRequest(BaseModel):
    game: str
    target_host: Optional[str] = None
    server_name: str = "default"
    backup_location: Optional[str] = None

class DeployWebAppRequest(BaseModel):
    app_type: str
    repo_url: str
    target_host: Optional[str] = None
    app_name: str = "default"
    custom_config: Optional[Dict[str, Any]] = None
    env_vars: Optional[Dict[str, str]] = None

class UpdateWebAppRequest(BaseModel):
    app_type: str
    target_host: Optional[str] = None
    app_name: str = "default"
    branch: str = "main"

class ConfigureNginxRequest(BaseModel):
    app_type: str
    target_host: Optional[str] = None
    app_name: str = "default"
    domain_name: str = "example.com"
    enable_ssl: bool = True

class SetupMonitoringRequest(BaseModel):
    app_type: str
    target_host: Optional[str] = None
    app_name: str = "default"
    monitoring_type: str = "prometheus"
    alert_email: Optional[str] = None

class TaskResponse(BaseModel):
    task_id: str
    status: str = "queued"
    message: str

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# FastAPI setup with startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize agents on startup
    try:
        logger.info("Initializing agents...")
        
        # Initialize system monitor
        await system_monitor.initialize()
        
        # Create agent instances
        agents["infrastructure"] = InfrastructureAgent()
        agents["game_server"] = GameServerAgent()
        agents["web_server"] = WebServerAgent()
        
        # Initialize agents
        for name, agent in agents.items():
            logger.info(f"Initializing {name} agent...")
            await agent.initialize()
            logger.info(f"{name.capitalize()} agent initialized")
        
        # Start the system status broadcast task
        asyncio.create_task(broadcast_system_status())
        asyncio.create_task(broadcast_task_updates())
    
    except Exception as e:
        logger.error(f"Error initializing agents: {e}")
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down agents...")
    for name, agent in agents.items():
        try:
            logger.info(f"Shutting down {name} agent...")
            await agent.shutdown()
            logger.info(f"{name.capitalize()} agent shut down")
        except Exception as e:
            logger.error(f"Error shutting down {name} agent: {e}")

# Create FastAPI app
app = FastAPI(
    title="Booner MCP API",
    description="API for infrastructure-as-code using AI agents with Model Context Protocol",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Periodic broadcast of system status
async def broadcast_system_status():
    """Periodically broadcast system status to all connected clients"""
    while True:
        if system_status_manager.active_connections:
            try:
                # Get system status
                status = await system_monitor.get_system_status()
                
                # Broadcast to all connected clients
                await system_status_manager.broadcast(json.dumps(status))
                
            except Exception as e:
                logger.error(f"Error broadcasting system status: {e}")
        
        # Wait before next update
        await asyncio.sleep(3)  # Update every 3 seconds

# Periodic broadcast of task updates
async def broadcast_task_updates():
    """Periodically broadcast task updates to all connected clients"""
    last_tasks = {}
    
    while True:
        if task_status_manager.active_connections and active_tasks != last_tasks:
            try:
                # Broadcast to all connected clients
                await task_status_manager.broadcast(json.dumps(active_tasks))
                
                # Update last_tasks
                last_tasks = active_tasks.copy()
                
            except Exception as e:
                logger.error(f"Error broadcasting task updates: {e}")
        
        # Wait before next update
        await asyncio.sleep(1)  # Check for updates every second

# Background task function to run agent tasks
async def run_agent_task(task_id: str, agent_name: str, method_name: str, **kwargs):
    try:
        active_tasks[task_id]["status"] = "running"
        
        # Get the agent instance
        agent = agents.get(agent_name)
        if not agent:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        # Get the method to call
        method = getattr(agent, method_name, None)
        if not method:
            raise ValueError(f"Unknown method: {method_name} for agent {agent_name}")
        
        # Call the method with the provided kwargs
        result = await method(**kwargs)
        
        # Update task status
        active_tasks[task_id]["status"] = "completed"
        active_tasks[task_id]["result"] = result
        
        logger.info(f"Task {task_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Error in task {task_id}: {e}")
        active_tasks[task_id]["status"] = "failed"
        active_tasks[task_id]["error"] = str(e)

# WebSocket endpoints
@app.websocket("/ws/system/status")
async def websocket_system_status(websocket: WebSocket):
    await system_status_manager.connect(websocket)
    
    # Send initial system status
    status = await system_monitor.get_system_status()
    await websocket.send_text(json.dumps(status))
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            # You can handle client messages here if needed
    except WebSocketDisconnect:
        system_status_manager.disconnect(websocket)
        logger.info("Client disconnected from system status WebSocket")

@app.websocket("/ws/tasks/updates")
async def websocket_task_updates(websocket: WebSocket):
    await task_status_manager.connect(websocket)
    
    # Send initial task status
    await websocket.send_text(json.dumps(active_tasks))
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            # You can handle client messages here if needed
    except WebSocketDisconnect:
        task_status_manager.disconnect(websocket)
        logger.info("Client disconnected from task updates WebSocket")

# API endpoints
@app.get("/")
async def root():
    return {"message": "Booner MCP API is running"}

@app.get("/system/status")
async def get_system_status():
    """GET endpoint for system status (fallback for WebSocket)"""
    return await system_monitor.get_system_status()

@app.get("/agents")
async def get_agents():
    return {"agents": list(agents.keys())}

@app.get("/tasks")
async def get_tasks():
    return {"tasks": active_tasks}

@app.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    task = active_tasks[task_id]
    return {
        "task_id": task_id,
        "status": task["status"],
        "result": task.get("result"),
        "error": task.get("error")
    }

# Game server endpoints
@app.post("/game/deploy", response_model=TaskResponse)
async def deploy_game_server(request: DeployGameServerRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    active_tasks[task_id] = {"status": "queued"}
    
    background_tasks.add_task(
        run_agent_task,
        task_id=task_id,
        agent_name="game_server",
        method_name="deploy_game_server",
        game=request.game,
        target_host=request.target_host,
        server_name=request.server_name,
        custom_config=request.custom_config
    )
    
    return {
        "task_id": task_id,
        "status": "queued",
        "message": f"Deploying {request.game} server '{request.server_name}'"
    }

@app.post("/game/update", response_model=TaskResponse)
async def update_game_server(request: UpdateGameServerRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    active_tasks[task_id] = {"status": "queued"}
    
    background_tasks.add_task(
        run_agent_task,
        task_id=task_id,
        agent_name="game_server",
        method_name="update_game_server",
        game=request.game,
        target_host=request.target_host,
        server_name=request.server_name
    )
    
    return {
        "task_id": task_id,
        "status": "queued",
        "message": f"Updating {request.game} server '{request.server_name}'"
    }

@app.post("/game/start", response_model=TaskResponse)
async def start_game_server(request: StartGameServerRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    active_tasks[task_id] = {"status": "queued"}
    
    background_tasks.add_task(
        run_agent_task,
        task_id=task_id,
        agent_name="game_server",
        method_name="start_game_server",
        game=request.game,
        target_host=request.target_host,
        server_name=request.server_name,
        custom_start_params=request.custom_start_params
    )
    
    return {
        "task_id": task_id,
        "status": "queued",
        "message": f"Starting {request.game} server '{request.server_name}'"
    }

@app.post("/game/stop", response_model=TaskResponse)
async def stop_game_server(request: StopGameServerRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    active_tasks[task_id] = {"status": "queued"}
    
    background_tasks.add_task(
        run_agent_task,
        task_id=task_id,
        agent_name="game_server",
        method_name="stop_game_server",
        game=request.game,
        target_host=request.target_host,
        server_name=request.server_name
    )
    
    return {
        "task_id": task_id,
        "status": "queued",
        "message": f"Stopping {request.game} server '{request.server_name}'"
    }

@app.post("/game/backup", response_model=TaskResponse)
async def backup_game_server(request: BackupGameServerRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    active_tasks[task_id] = {"status": "queued"}
    
    background_tasks.add_task(
        run_agent_task,
        task_id=task_id,
        agent_name="game_server",
        method_name="backup_game_server",
        game=request.game,
        target_host=request.target_host,
        server_name=request.server_name,
        backup_location=request.backup_location
    )
    
    return {
        "task_id": task_id,
        "status": "queued",
        "message": f"Backing up {request.game} server '{request.server_name}'"
    }

# Web server endpoints
@app.post("/web/deploy", response_model=TaskResponse)
async def deploy_web_app(request: DeployWebAppRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    active_tasks[task_id] = {"status": "queued"}
    
    background_tasks.add_task(
        run_agent_task,
        task_id=task_id,
        agent_name="web_server",
        method_name="deploy_web_app",
        app_type=request.app_type,
        repo_url=request.repo_url,
        target_host=request.target_host,
        app_name=request.app_name,
        custom_config=request.custom_config,
        env_vars=request.env_vars
    )
    
    return {
        "task_id": task_id,
        "status": "queued",
        "message": f"Deploying {request.app_type} application '{request.app_name}' from {request.repo_url}"
    }

@app.post("/web/update", response_model=TaskResponse)
async def update_web_app(request: UpdateWebAppRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    active_tasks[task_id] = {"status": "queued"}
    
    background_tasks.add_task(
        run_agent_task,
        task_id=task_id,
        agent_name="web_server",
        method_name="update_web_app",
        app_type=request.app_type,
        target_host=request.target_host,
        app_name=request.app_name,
        branch=request.branch
    )
    
    return {
        "task_id": task_id,
        "status": "queued",
        "message": f"Updating {request.app_type} application '{request.app_name}' from branch {request.branch}"
    }

@app.post("/web/nginx", response_model=TaskResponse)
async def configure_nginx(request: ConfigureNginxRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    active_tasks[task_id] = {"status": "queued"}
    
    background_tasks.add_task(
        run_agent_task,
        task_id=task_id,
        agent_name="web_server",
        method_name="configure_nginx_proxy",
        app_type=request.app_type,
        target_host=request.target_host,
        app_name=request.app_name,
        domain_name=request.domain_name,
        enable_ssl=request.enable_ssl
    )
    
    return {
        "task_id": task_id,
        "status": "queued",
        "message": f"Configuring Nginx for {request.app_type} application '{request.app_name}' with domain {request.domain_name}"
    }

@app.post("/web/monitoring", response_model=TaskResponse)
async def setup_monitoring(request: SetupMonitoringRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    active_tasks[task_id] = {"status": "queued"}
    
    background_tasks.add_task(
        run_agent_task,
        task_id=task_id,
        agent_name="web_server",
        method_name="setup_monitoring",
        app_type=request.app_type,
        target_host=request.target_host,
        app_name=request.app_name,
        monitoring_type=request.monitoring_type,
        alert_email=request.alert_email
    )
    
    return {
        "task_id": task_id,
        "status": "queued",
        "message": f"Setting up {request.monitoring_type} monitoring for {request.app_type} application '{request.app_name}'"
    }

# Infrastructure tasks endpoint
@app.post("/infrastructure/task", response_model=TaskResponse)
async def run_infrastructure_task(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    
    if "task" not in data:
        raise HTTPException(status_code=400, detail="Task description required")
    
    task_description = data["task"]
    task_id = str(uuid.uuid4())
    active_tasks[task_id] = {"status": "queued"}
    
    background_tasks.add_task(
        run_agent_task,
        task_id=task_id,
        agent_name="infrastructure",
        method_name="run_task",
        task_description=task_description
    )
    
    return {
        "task_id": task_id,
        "status": "queued",
        "message": f"Running infrastructure task: {task_description[:50]}{'...' if len(task_description) > 50 else ''}"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app_with_websockets:app", host="0.0.0.0", port=8000, reload=True)
