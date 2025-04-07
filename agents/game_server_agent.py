import logging
import json
import asyncio
import sys
import os
from typing import Dict, List, Optional, Any

# Add the parent directory to the Python path so we can import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.base_agent import BaseAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GameServerAgent(BaseAgent):
    """An agent specialized in game server deployment and management."""
    
    def __init__(
        self,
        name: str = "GameServerAgent",
        model: str = "mixtral",
        config_path: str = "../config/mcp_config.json"
    ):
        system_prompt = (
            "You are a game server management AI agent. "
            "You can deploy, configure, and manage various game servers including "
            "CS2, Killing Floor, Minecraft, and others. "
            "You have access to filesystem, git, and other tools through the Model Context Protocol. "
            "When given a task, think step-by-step about how to accomplish it using the available infrastructure. "
            "Format actions as JSON with a 'type' field and 'params' object."
        )
        
        super().__init__(name, model, system_prompt, config_path)
        
        # This agent requires these MCP servers
        self.required_servers = ["filesystem", "git", "time"]
        
        # Game server configurations
        self.game_configs = {
            "cs2": {
                "install_script": "steamcmd +login anonymous +app_update 730 +quit",
                "start_command": "./srcds_run -game csgo -console -usercon +game_type 0 +game_mode 1 +mapgroup mg_active +map de_dust2",
                "required_ports": [27015, 27016, 27017, 27018, 27019, 27020],
                "min_ram": 4096,  # MB
                "recommended_ram": 8192  # MB
            },
            "minecraft": {
                "install_script": "wget https://launcher.mojang.com/v1/objects/a16d67e5807f57fc4e550299cf20226194497dc2/server.jar -O minecraft_server.jar",
                "start_command": "java -Xmx4G -Xms2G -jar minecraft_server.jar nogui",
                "required_ports": [25565],
                "min_ram": 2048,  # MB
                "recommended_ram": 4096  # MB
            },
            "killingfloor2": {
                "install_script": "steamcmd +login anonymous +app_update 232130 +quit",
                "start_command": "./KFGame/Binaries/Win64/KFGameSteamServer.bin.x86_64 kf-bioticslab",
                "required_ports": [7777, 27015, 20560, 123],
                "min_ram": 4096,  # MB
                "recommended_ram": 8192  # MB
            }
        }
    
    async def deploy_game_server(
        self,
        game: str,
        target_host: Optional[str] = None,
        server_name: str = "default",
        custom_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Deploy a game server.
        
        Args:
            game: Type of game server to deploy
            target_host: Host to deploy to (if None, uses the default from config)
            server_name: Name for the server
            custom_config: Custom configuration options
            
        Returns:
            Result of the deployment
        """
        if game.lower() not in self.game_configs:
            return {
                "success": False,
                "error": f"Unsupported game: {game}. Supported games: {', '.join(self.game_configs.keys())}"
            }
        
        # Get the default game config
        game_config = self.game_configs[game.lower()]
        
        # Override with custom config if provided
        if custom_config:
            for key, value in custom_config.items():
                if key in game_config:
                    game_config[key] = value
        
        # Get the target host from config if not specified
        if not target_host:
            target_host = self._get_default_target_host("game_server")
        
        # Create a deployment task for the agent
        task_description = (
            f"Deploy a {game} server on {target_host} with name '{server_name}'. "
            f"Use the installation script: {game_config['install_script']} "
            f"And start command: {game_config['start_command']} "
            f"Required ports: {game_config['required_ports']} "
            f"Ensure the server has at least {game_config['min_ram']}MB of RAM available."
        )
        
        # Run the deployment task using the agent
        result = await self.run_task(task_description)
        
        return {
            "game": game,
            "server_name": server_name,
            "target_host": target_host,
            "config": game_config,
            "deployment_result": result
        }
    
    def _get_default_target_host(self, host_type: str) -> str:
        """Get the default target host for a specific type from config."""
        try:
            with open(self.mcp_connector.config_path, 'r') as f:
                config = json.load(f)
                return config.get("agents", {}).get("deployment_targets", {}).get(host_type, {}).get("host", "localhost")
        except:
            return "localhost"
    
    async def update_game_server(
        self,
        game: str,
        target_host: Optional[str] = None,
        server_name: str = "default"
    ) -> Dict[str, Any]:
        """
        Update a game server to the latest version.
        
        Args:
            game: Type of game server to update
            target_host: Host to update on (if None, uses the default from config)
            server_name: Name of the server to update
            
        Returns:
            Result of the update
        """
        if game.lower() not in self.game_configs:
            return {
                "success": False,
                "error": f"Unsupported game: {game}. Supported games: {', '.join(self.game_configs.keys())}"
            }
        
        # Get the game config
        game_config = self.game_configs[game.lower()]
        
        # Get the target host from config if not specified
        if not target_host:
            target_host = self._get_default_target_host("game_server")
        
        # Create an update task for the agent
        task_description = (
            f"Update the {game} server named '{server_name}' on {target_host}. "
            f"Use the update script: {game_config['install_script']} "
            f"Ensure proper backup before updating."
        )
        
        # Run the update task using the agent
        result = await self.run_task(task_description)
        
        return {
            "game": game,
            "server_name": server_name,
            "target_host": target_host,
            "update_result": result
        }
    
    async def start_game_server(
        self,
        game: str,
        target_host: Optional[str] = None,
        server_name: str = "default",
        custom_start_params: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Start a game server.
        
        Args:
            game: Type of game server to start
            target_host: Host to start on (if None, uses the default from config)
            server_name: Name of the server to start
            custom_start_params: Custom startup parameters
            
        Returns:
            Result of starting the server
        """
        if game.lower() not in self.game_configs:
            return {
                "success": False,
                "error": f"Unsupported game: {game}. Supported games: {', '.join(self.game_configs.keys())}"
            }
        
        # Get the game config
        game_config = self.game_configs[game.lower()]
        
        # Get the target host from config if not specified
        if not target_host:
            target_host = self._get_default_target_host("game_server")
        
        # Get the start command, with custom params if provided
        start_command = game_config["start_command"]
        if custom_start_params:
            start_command += f" {custom_start_params}"
        
        # Create a start task for the agent
        task_description = (
            f"Start the {game} server named '{server_name}' on {target_host}. "
            f"Use the command: {start_command} "
            f"Ensure all required ports {game_config['required_ports']} are available."
        )
        
        # Run the start task using the agent
        result = await self.run_task(task_description)
        
        return {
            "game": game,
            "server_name": server_name,
            "target_host": target_host,
            "start_command": start_command,
            "start_result": result
        }
    
    async def stop_game_server(
        self,
        game: str,
        target_host: Optional[str] = None,
        server_name: str = "default"
    ) -> Dict[str, Any]:
        """
        Stop a game server.
        
        Args:
            game: Type of game server to stop
            target_host: Host to stop on (if None, uses the default from config)
            server_name: Name of the server to stop
            
        Returns:
            Result of stopping the server
        """
        # Get the target host from config if not specified
        if not target_host:
            target_host = self._get_default_target_host("game_server")
        
        # Create a stop task for the agent
        task_description = (
            f"Stop the {game} server named '{server_name}' on {target_host}. "
            f"Ensure proper shutdown to prevent data corruption."
        )
        
        # Run the stop task using the agent
        result = await self.run_task(task_description)
        
        return {
            "game": game,
            "server_name": server_name,
            "target_host": target_host,
            "stop_result": result
        }
    
    async def backup_game_server(
        self,
        game: str,
        target_host: Optional[str] = None,
        server_name: str = "default",
        backup_location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Backup a game server.
        
        Args:
            game: Type of game server to backup
            target_host: Host to backup on (if None, uses the default from config)
            server_name: Name of the server to backup
            backup_location: Location to store the backup (if None, uses default)
            
        Returns:
            Result of backing up the server
        """
        # Get the target host from config if not specified
        if not target_host:
            target_host = self._get_default_target_host("game_server")
        
        # Use the NFS mount point as default backup location if not specified
        if not backup_location:
            try:
                with open(self.mcp_connector.config_path, 'r') as f:
                    config = json.load(f)
                    backup_location = config.get("storage", {}).get("truenas", {}).get("nfs_mount_points", {}).get("hdd", "/mnt/truenas/hdd")
            except:
                backup_location = "/mnt/backups"
        
        # Create a backup task for the agent
        task_description = (
            f"Backup the {game} server named '{server_name}' on {target_host}. "
            f"Store the backup at {backup_location}/{game}_{server_name}_backup_$(date +%Y%m%d_%H%M%S). "
            f"Ensure the server is in a consistent state before backup."
        )
        
        # Run the backup task using the agent
        result = await self.run_task(task_description)
        
        return {
            "game": game,
            "server_name": server_name,
            "target_host": target_host,
            "backup_location": backup_location,
            "backup_result": result
        }

async def test_game_server_agent():
    """Test the game server agent."""
    agent = GameServerAgent()
    
    try:
        # Initialize the agent
        initialized = await agent.initialize()
        if not initialized:
            logger.error("Failed to initialize agent")
            return
        
        # Run a test deployment task
        logger.info("Running test deployment task...")
        result = await agent.deploy_game_server(
            game="minecraft",
            server_name="test_server",
            custom_config={"recommended_ram": 6144}
        )
        
        logger.info(f"Deployment result: {json.dumps(result, indent=2)}")
        
    except Exception as e:
        logger.error(f"Error testing game server agent: {e}")
    
    finally:
        # Shutdown the agent
        await agent.shutdown()

if __name__ == "__main__":
    asyncio.run(test_game_server_agent())
