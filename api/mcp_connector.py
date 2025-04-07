import json
import logging
import os
import subprocess
import asyncio
from typing import Dict, List, Optional, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPConnector:
    """Connector for managing MCP servers and interacting with them."""
    
    def __init__(self, config_path: str = "../config/mcp_config.json"):
        """
        Initialize the MCP connector.
        
        Args:
            config_path: Path to the MCP configuration file
        """
        self.config_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), config_path)
        )
        self.config = self._load_config()
        self.running_servers = {}
    
    def _load_config(self) -> Dict[str, Any]:
        """Load the MCP configuration from the config file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading MCP config: {e}")
            return {"mcp": {"servers": {}}}
    
    async def start_server(self, server_name: str) -> bool:
        """
        Start an MCP server.
        
        Args:
            server_name: Name of the server to start
            
        Returns:
            Whether the server was successfully started
        """
        if server_name not in self.config["mcp"]["servers"]:
            logger.error(f"Server {server_name} not found in configuration")
            return False
        
        if server_name in self.running_servers:
            logger.info(f"Server {server_name} is already running")
            return True
        
        server_config = self.config["mcp"]["servers"][server_name]
        if not server_config.get("enabled", True):
            logger.warning(f"Server {server_name} is disabled in configuration")
            return False
        
        try:
            command = [server_config["command"]] + server_config["args"]
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            self.running_servers[server_name] = {
                "process": process,
                "command": command,
                "started_at": asyncio.get_event_loop().time()
            }
            
            # Start log monitoring in the background
            asyncio.create_task(self._monitor_logs(server_name, process))
            
            logger.info(f"Started MCP server {server_name} (PID: {process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"Error starting MCP server {server_name}: {e}")
            return False
    
    async def _monitor_logs(self, server_name: str, process: asyncio.subprocess.Process):
        """Monitor logs from the server process."""
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            
            log_line = line.decode('utf-8').strip()
            logger.info(f"[{server_name}] {log_line}")
    
    async def stop_server(self, server_name: str) -> bool:
        """
        Stop an MCP server.
        
        Args:
            server_name: Name of the server to stop
            
        Returns:
            Whether the server was successfully stopped
        """
        if server_name not in self.running_servers:
            logger.warning(f"Server {server_name} is not running")
            return True
        
        try:
            process_info = self.running_servers[server_name]
            process = process_info["process"]
            
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning(f"Server {server_name} did not terminate gracefully, killing...")
                process.kill()
                await process.wait()
            
            del self.running_servers[server_name]
            logger.info(f"Stopped MCP server {server_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping MCP server {server_name}: {e}")
            return False
    
    async def start_all_servers(self) -> Dict[str, bool]:
        """
        Start all enabled MCP servers.
        
        Returns:
            Dictionary mapping server names to whether they were successfully started
        """
        results = {}
        for server_name, server_config in self.config["mcp"]["servers"].items():
            if server_config.get("enabled", True):
                results[server_name] = await self.start_server(server_name)
        
        return results
    
    async def stop_all_servers(self) -> Dict[str, bool]:
        """
        Stop all running MCP servers.
        
        Returns:
            Dictionary mapping server names to whether they were successfully stopped
        """
        results = {}
        for server_name in list(self.running_servers.keys()):
            results[server_name] = await self.stop_server(server_name)
        
        return results
    
    def get_running_servers(self) -> List[str]:
        """Get a list of currently running MCP servers."""
        return list(self.running_servers.keys())
    
    def get_available_servers(self) -> List[str]:
        """Get a list of all available MCP servers from the configuration."""
        return list(self.config["mcp"]["servers"].keys())

async def test_mcp_connector():
    """Test the MCP connector."""
    connector = MCPConnector()
    
    try:
        # List available servers
        available = connector.get_available_servers()
        logger.info(f"Available MCP servers: {available}")
        
        if available:
            # Start a server (using the first available)
            test_server = available[0]
            logger.info(f"Starting MCP server {test_server}...")
            started = await connector.start_server(test_server)
            
            if started:
                logger.info(f"MCP server {test_server} started successfully")
                
                # Let it run for a few seconds
                await asyncio.sleep(5)
                
                # Stop the server
                logger.info(f"Stopping MCP server {test_server}...")
                stopped = await connector.stop_server(test_server)
                
                if stopped:
                    logger.info(f"MCP server {test_server} stopped successfully")
                else:
                    logger.error(f"Failed to stop MCP server {test_server}")
            else:
                logger.error(f"Failed to start MCP server {test_server}")
    
    except Exception as e:
        logger.error(f"Error during MCP connector test: {e}")

if __name__ == "__main__":
    asyncio.run(test_mcp_connector())
