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

class WebServerAgent(BaseAgent):
    """An agent specialized in web server deployment and management."""
    
    def __init__(
        self,
        name: str = "WebServerAgent",
        model: str = "mixtral",
        config_path: str = "../config/mcp_config.json"
    ):
        system_prompt = (
            "You are a web server management AI agent. "
            "You can deploy, configure, and manage various web applications including "
            "NextJS, Express, Django, Flask, and static sites. "
            "You have access to filesystem, git, and other tools through the Model Context Protocol. "
            "When given a task, think step-by-step about how to accomplish it using the available infrastructure. "
            "Format actions as JSON with a 'type' field and 'params' object."
        )
        
        super().__init__(name, model, system_prompt, config_path)
        
        # This agent requires these MCP servers
        self.required_servers = ["filesystem", "git", "time"]
        
        # Web server configurations
        self.web_configs = {
            "nextjs": {
                "setup_commands": [
                    "npm install",
                    "npm run build"
                ],
                "start_command": "npm start",
                "required_ports": [3000],
                "default_node_version": "18.x",
                "environment_vars": {
                    "NODE_ENV": "production",
                    "PORT": "3000"
                }
            },
            "express": {
                "setup_commands": [
                    "npm install"
                ],
                "start_command": "node server.js",
                "required_ports": [3000],
                "default_node_version": "18.x",
                "environment_vars": {
                    "NODE_ENV": "production",
                    "PORT": "3000"
                }
            },
            "django": {
                "setup_commands": [
                    "pip install -r requirements.txt",
                    "python manage.py migrate",
                    "python manage.py collectstatic --noinput"
                ],
                "start_command": "gunicorn myproject.wsgi:application --bind 0.0.0.0:8000",
                "required_ports": [8000],
                "default_python_version": "3.10",
                "environment_vars": {
                    "DJANGO_SETTINGS_MODULE": "myproject.settings",
                    "DJANGO_SECRET_KEY": "placeholder_secret_key",
                    "DATABASE_URL": "sqlite:///db.sqlite3"
                }
            },
            "flask": {
                "setup_commands": [
                    "pip install -r requirements.txt"
                ],
                "start_command": "gunicorn app:app --bind 0.0.0.0:5000",
                "required_ports": [5000],
                "default_python_version": "3.10",
                "environment_vars": {
                    "FLASK_ENV": "production",
                    "FLASK_APP": "app.py"
                }
            },
            "static": {
                "setup_commands": [],
                "start_command": "npx serve -s build -l 3000",
                "required_ports": [3000],
                "environment_vars": {}
            }
        }
    
    async def deploy_web_app(
        self,
        app_type: str,
        repo_url: str,
        target_host: Optional[str] = None,
        app_name: str = "default",
        custom_config: Optional[Dict[str, Any]] = None,
        env_vars: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Deploy a web application.
        
        Args:
            app_type: Type of web application (nextjs, express, django, etc.)
            repo_url: Git repository URL for the application
            target_host: Host to deploy to (if None, uses the default from config)
            app_name: Name for the application
            custom_config: Custom configuration options
            env_vars: Environment variables for the application
            
        Returns:
            Result of the deployment
        """
        if app_type.lower() not in self.web_configs:
            return {
                "success": False,
                "error": f"Unsupported application type: {app_type}. Supported types: {', '.join(self.web_configs.keys())}"
            }
        
        # Get the default web config
        web_config = self.web_configs[app_type.lower()]
        
        # Override with custom config if provided
        if custom_config:
            for key, value in custom_config.items():
                if key in web_config:
                    web_config[key] = value
        
        # Merge environment variables
        environment_vars = dict(web_config.get("environment_vars", {}))
        if env_vars:
            environment_vars.update(env_vars)
        
        # Get the target host from config if not specified
        if not target_host:
            target_host = self._get_default_target_host("web_server")
        
        # Create a deployment task for the agent
        task_description = (
            f"Deploy a {app_type} application from {repo_url} on {target_host} with name '{app_name}'. "
            f"Setup commands: {', '.join(web_config['setup_commands'])} "
            f"Start command: {web_config['start_command']} "
            f"Required ports: {web_config['required_ports']} "
            f"Environment variables: {json.dumps(environment_vars)}"
        )
        
        # Run the deployment task using the agent
        result = await self.run_task(task_description)
        
        return {
            "app_type": app_type,
            "app_name": app_name,
            "repo_url": repo_url,
            "target_host": target_host,
            "config": web_config,
            "environment_vars": environment_vars,
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
    
    async def update_web_app(
        self,
        app_type: str,
        target_host: Optional[str] = None,
        app_name: str = "default",
        branch: str = "main"
    ) -> Dict[str, Any]:
        """
        Update a web application from its git repository.
        
        Args:
            app_type: Type of web application
            target_host: Host to update on (if None, uses the default from config)
            app_name: Name of the application to update
            branch: Git branch to update from
            
        Returns:
            Result of the update
        """
        if app_type.lower() not in self.web_configs:
            return {
                "success": False,
                "error": f"Unsupported application type: {app_type}. Supported types: {', '.join(self.web_configs.keys())}"
            }
        
        # Get the web config
        web_config = self.web_configs[app_type.lower()]
        
        # Get the target host from config if not specified
        if not target_host:
            target_host = self._get_default_target_host("web_server")
        
        # Create an update task for the agent
        task_description = (
            f"Update the {app_type} application named '{app_name}' on {target_host} from the {branch} branch. "
            f"Execute git pull, then run the setup commands: {', '.join(web_config['setup_commands'])} "
            f"Finally, restart the application with: {web_config['start_command']} "
            f"Ensure proper backup before updating."
        )
        
        # Run the update task using the agent
        result = await self.run_task(task_description)
        
        return {
            "app_type": app_type,
            "app_name": app_name,
            "target_host": target_host,
            "branch": branch,
            "update_result": result
        }
    
    async def configure_nginx_proxy(
        self,
        app_type: str,
        target_host: Optional[str] = None,
        app_name: str = "default",
        domain_name: str = "example.com",
        enable_ssl: bool = True
    ) -> Dict[str, Any]:
        """
        Configure Nginx as a reverse proxy for a web application.
        
        Args:
            app_type: Type of web application
            target_host: Host to configure Nginx on (if None, uses the default from config)
            app_name: Name of the application
            domain_name: Domain name for the application
            enable_ssl: Whether to enable SSL with Let's Encrypt
            
        Returns:
            Result of the Nginx configuration
        """
        if app_type.lower() not in self.web_configs:
            return {
                "success": False,
                "error": f"Unsupported application type: {app_type}. Supported types: {', '.join(self.web_configs.keys())}"
            }
        
        # Get the web config to determine the port
        web_config = self.web_configs[app_type.lower()]
        app_port = web_config.get("required_ports", [3000])[0]
        
        # Get the target host from config if not specified
        if not target_host:
            target_host = self._get_default_target_host("web_server")
        
        # Create a Nginx configuration task for the agent
        ssl_text = "Enable SSL using Lets Encrypt" if enable_ssl else "Use HTTP only (no SSL)"
        task_description = (
            f"Configure Nginx as a reverse proxy for the {app_type} application named '{app_name}' on {target_host}. "
            f"Use domain name: {domain_name} "
            f"Proxy to the application running on port {app_port} "
            f"{ssl_text} "
            f"Ensure proper HTTP headers and caching for a {app_type} application."
        )
        
        # Run the Nginx configuration task using the agent
        result = await self.run_task(task_description)
        
        return {
            "app_type": app_type,
            "app_name": app_name,
            "target_host": target_host,
            "domain_name": domain_name,
            "enable_ssl": enable_ssl,
            "app_port": app_port,
            "nginx_config_result": result
        }
    
    async def setup_monitoring(
        self,
        app_type: str,
        target_host: Optional[str] = None,
        app_name: str = "default",
        monitoring_type: str = "prometheus",
        alert_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Set up monitoring for a web application.
        
        Args:
            app_type: Type of web application
            target_host: Host to set up monitoring on (if None, uses the default from config)
            app_name: Name of the application
            monitoring_type: Type of monitoring to set up (prometheus, grafana, etc.)
            alert_email: Email to send alerts to
            
        Returns:
            Result of setting up monitoring
        """
        # Get the target host from config if not specified
        if not target_host:
            target_host = self._get_default_target_host("web_server")
        
        # Create a monitoring setup task for the agent
        task_description = (
            f"Set up {monitoring_type} monitoring for the {app_type} application named '{app_name}' on {target_host}. "
            f"Monitor CPU, memory, disk usage, and application-specific metrics. "
            f"{'Configure alerts to be sent to ' + alert_email if alert_email else 'No email alerts required'} "
            f"Ensure dashboard and visualization setup."
        )
        
        # Run the monitoring setup task using the agent
        result = await self.run_task(task_description)
        
        return {
            "app_type": app_type,
            "app_name": app_name,
            "target_host": target_host,
            "monitoring_type": monitoring_type,
            "alert_email": alert_email,
            "monitoring_setup_result": result
        }

async def test_web_server_agent():
    """Test the web server agent."""
    agent = WebServerAgent()
    
    try:
        # Initialize the agent
        initialized = await agent.initialize()
        if not initialized:
            logger.error("Failed to initialize agent")
            return
        
        # Run a test deployment task
        logger.info("Running test deployment task...")
        result = await agent.deploy_web_app(
            app_type="nextjs",
            repo_url="https://github.com/example/nextjs-app.git",
            app_name="test_nextjs",
            env_vars={"API_URL": "https://api.example.com"}
        )
        
        logger.info(f"Deployment result: {json.dumps(result, indent=2)}")
        
    except Exception as e:
        logger.error(f"Error testing web server agent: {e}")
    
    finally:
        # Shutdown the agent
        await agent.shutdown()

if __name__ == "__main__":
    asyncio.run(test_web_server_agent())
