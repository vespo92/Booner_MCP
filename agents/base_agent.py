import logging
import json
import asyncio
import sys
import os
from typing import Dict, List, Optional, Any, Callable

# Add the parent directory to the Python path so we can import from api
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.ollama_client import OllamaClient
from api.mcp_connector import MCPConnector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseAgent:
    """Base class for AI agents that can perform infrastructure tasks."""
    
    def __init__(
        self,
        name: str,
        model: str = "mixtral",
        system_prompt: Optional[str] = None,
        config_path: str = "../config/mcp_config.json"
    ):
        """
        Initialize the base agent.
        
        Args:
            name: Name of the agent
            model: Model to use for this agent
            system_prompt: System prompt for the agent
            config_path: Path to the configuration file
        """
        self.name = name
        self.model = model
        self.system_prompt = system_prompt or self._get_default_system_prompt()
        self.ollama_client = None
        self.mcp_connector = MCPConnector(config_path)
        self.conversation_history = []
        self.required_servers = []
        
    async def initialize(self) -> bool:
        """Initialize the agent by setting up clients and required servers."""
        try:
            # Initialize Ollama client
            base_url = self._get_ollama_base_url()
            self.ollama_client = OllamaClient(base_url)
            await self.ollama_client.__aenter__()
            
            # Start required MCP servers
            for server in self.required_servers:
                success = await self.mcp_connector.start_server(server)
                if not success:
                    logger.error(f"Failed to start required MCP server: {server}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing agent {self.name}: {e}")
            return False
    
    async def shutdown(self) -> None:
        """Shutdown the agent by cleaning up resources."""
        try:
            # Close Ollama client
            if self.ollama_client:
                await self.ollama_client.__aexit__(None, None, None)
            
            # Stop any MCP servers that were started
            for server in self.required_servers:
                await self.mcp_connector.stop_server(server)
                
        except Exception as e:
            logger.error(f"Error shutting down agent {self.name}: {e}")
    
    def _get_ollama_base_url(self) -> str:
        """Get the Ollama base URL from the configuration."""
        try:
            with open(self.mcp_connector.config_path, 'r') as f:
                config = json.load(f)
                return config.get("ollama", {}).get("base_url", "http://localhost:11434")
        except:
            return "http://localhost:11434"
    
    def _get_default_system_prompt(self) -> str:
        """Get the default system prompt for the agent."""
        return (
            f"You are {self.name}, an AI agent that can perform infrastructure tasks. "
            "You have access to various tools through the Model Context Protocol (MCP). "
            "Think step-by-step and clearly explain your actions."
        )
    
    async def run_task(self, task_description: str) -> Dict[str, Any]:
        """
        Run a task using the agent.
        
        Args:
            task_description: Description of the task to perform
            
        Returns:
            Result of the task
        """
        # Add the task to conversation history
        self.conversation_history.append({"role": "user", "content": task_description})
        
        # Generate a completion with the task
        prompt = self._format_prompt(task_description)
        
        try:
            response = await self.ollama_client.generate(
                model=self.model,
                prompt=prompt,
                system=self.system_prompt,
                temperature=0.7,
                max_tokens=2048
            )
            
            # Add the response to conversation history
            self.conversation_history.append({"role": "assistant", "content": response["response"]})
            
            # Parse any actions from the response
            actions = self._parse_actions(response["response"])
            
            # Execute actions
            action_results = await self._execute_actions(actions)
            
            return {
                "task": task_description,
                "response": response["response"],
                "actions": actions,
                "action_results": action_results
            }
            
        except Exception as e:
            logger.error(f"Error running task for agent {self.name}: {e}")
            return {
                "task": task_description,
                "error": str(e),
                "success": False
            }
    
    def _format_prompt(self, task_description: str) -> str:
        """Format the prompt for the model."""
        # Format conversation history
        formatted_history = ""
        for message in self.conversation_history:
            role = message["role"]
            content = message["content"]
            
            if role == "user":
                formatted_history += f"User: {content}\n\n"
            elif role == "assistant":
                formatted_history += f"Assistant: {content}\n\n"
        
        # Add the current task
        formatted_history += f"User: {task_description}\n\nAssistant:"
        
        return formatted_history
    
    def _parse_actions(self, response: str) -> List[Dict[str, Any]]:
        """
        Parse actions from the model's response.
        
        Returns:
            List of actions to execute
        """
        # This is a simple implementation - in a real system, you would use
        # a more sophisticated parser to extract actions from the response
        actions = []
        
        # Look for action blocks (e.g., ```action ... ```)
        lines = response.split('\n')
        in_action_block = False
        current_action = ""
        
        for line in lines:
            if line.strip().startswith("```action") or line.strip().startswith("```json"):
                in_action_block = True
                current_action = ""
            elif line.strip() == "```" and in_action_block:
                in_action_block = False
                try:
                    action_data = json.loads(current_action)
                    actions.append(action_data)
                except:
                    logger.warning(f"Failed to parse action: {current_action}")
            elif in_action_block:
                current_action += line + "\n"
        
        return actions
    
    async def _execute_actions(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute a list of actions.
        
        Args:
            actions: List of actions to execute
            
        Returns:
            Results of executing the actions
        """
        results = []
        
        for action in actions:
            action_type = action.get("type")
            action_params = action.get("params", {})
            
            result = {
                "action": action,
                "success": False,
                "result": None,
                "error": None
            }
            
            try:
                if action_type == "deploy_web_server":
                    # Example action implementation
                    result["result"] = "Web server deployment simulated"
                    result["success"] = True
                elif action_type == "deploy_game_server":
                    # Example action implementation
                    result["result"] = f"Game server deployment simulated for {action_params.get('game', 'unknown')}"
                    result["success"] = True
                elif action_type == "backup_database":
                    # Example action implementation
                    result["result"] = f"Database backup simulated for {action_params.get('database', 'unknown')}"
                    result["success"] = True
                else:
                    result["error"] = f"Unknown action type: {action_type}"
            
            except Exception as e:
                result["error"] = str(e)
            
            results.append(result)
        
        return results

class InfrastructureAgent(BaseAgent):
    """An agent specialized in infrastructure management."""
    
    def __init__(
        self,
        name: str = "InfrastructureAgent",
        model: str = "mixtral",
        config_path: str = "../config/mcp_config.json"
    ):
        system_prompt = (
            "You are an infrastructure management AI agent. "
            "You can deploy and manage web servers, game servers, and databases. "
            "You have access to filesystem, git, and other tools through the Model Context Protocol. "
            "When given a task, think step-by-step about how to accomplish it using the available infrastructure. "
            "Format actions as JSON with a 'type' field and 'params' object."
        )
        
        super().__init__(name, model, system_prompt, config_path)
        
        # This agent requires these MCP servers
        self.required_servers = ["filesystem", "git", "time"]

async def test_agent():
    """Test the infrastructure agent."""
    agent = InfrastructureAgent()
    
    try:
        # Initialize the agent
        initialized = await agent.initialize()
        if not initialized:
            logger.error("Failed to initialize agent")
            return
        
        # Run a test task
        logger.info("Running test task...")
        result = await agent.run_task(
            "Set up a basic web server for hosting a NextJS application"
        )
        
        logger.info(f"Task result: {json.dumps(result, indent=2)}")
        
    except Exception as e:
        logger.error(f"Error testing agent: {e}")
    
    finally:
        # Shutdown the agent
        await agent.shutdown()

if __name__ == "__main__":
    asyncio.run(test_agent())
