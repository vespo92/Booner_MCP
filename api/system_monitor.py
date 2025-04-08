import os
import sys
import psutil
import platform
import asyncio
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class SystemMonitor:
    """System monitoring utility for Booner MCP"""
    
    def __init__(self):
        self.previous_cpu = None
        self.previous_network = {}
        self.deployment_targets = []
        
    async def initialize(self):
        """Initialize the system monitor"""
        try:
            # Read deployment targets from configuration
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "config",
                "mcp_config.json"
            )
            
            if os.path.exists(config_path):
                import json
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    if "deployment_targets" in config:
                        self.deployment_targets = config["deployment_targets"]
            
            logger.info(f"System monitor initialized with {len(self.deployment_targets)} deployment targets")
            return True
        except Exception as e:
            logger.error(f"Error initializing system monitor: {e}")
            return False
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get current system status information"""
        try:
            # Get CPU information
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            cpu_freq_text = f"{cpu_freq.current:.2f} MHz" if cpu_freq else "Unknown"
            
            # Get memory information
            memory = psutil.virtual_memory()
            memory_total = memory.total / (1024 * 1024 * 1024)  # GB
            memory_used = memory.used / (1024 * 1024 * 1024)    # GB
            memory_percent = memory.percent
            
            # Get disk information
            disk = psutil.disk_usage('/')
            disk_total = disk.total / (1024 * 1024 * 1024)  # GB
            disk_used = disk.used / (1024 * 1024 * 1024)    # GB
            disk_percent = disk.percent
            
            # Check GPU information if available
            gpu_info = self._get_gpu_info()
            
            # Format main server info
            main_server = {
                "cpu": f"{platform.processor()} ({cpu_count} cores @ {cpu_freq_text}, {cpu_percent}% used)",
                "gpu": gpu_info or "None",
                "ram": f"{memory_total:.2f} GB ({memory_percent}% used)",
                "disk": f"{disk_total:.2f} GB ({disk_percent}% used)",
                "status": "active"
            }
            
            # Get deployment targets info
            deployment_targets = await self._get_deployment_targets_status()
            
            return {
                "main_server": main_server,
                "deployment_targets": deployment_targets
            }
        
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                "main_server": {
                    "cpu": "Error retrieving CPU info",
                    "gpu": "Error retrieving GPU info",
                    "ram": "Error retrieving RAM info",
                    "disk": "Error retrieving disk info",
                    "status": "error"
                },
                "deployment_targets": []
            }
    
    def _get_gpu_info(self) -> Optional[str]:
        """Attempt to get GPU information"""
        try:
            # Try nvidia-smi for NVIDIA GPUs
            if sys.platform == "linux" or sys.platform == "darwin":
                import subprocess
                try:
                    output = subprocess.check_output(["nvidia-smi", "--query-gpu=name,memory.total,memory.used,temperature.gpu", "--format=csv,noheader"], 
                                                    universal_newlines=True)
                    if output:
                        # Format output
                        gpu_data = output.strip().split(',')
                        return f"{gpu_data[0].strip()} ({gpu_data[2].strip()}/{gpu_data[1].strip()} @ {gpu_data[3].strip()}°C)"
                except (subprocess.SubprocessError, FileNotFoundError):
                    pass
            
            # Add alternative GPU detection methods here if needed
            return None
        
        except Exception as e:
            logger.debug(f"Error getting GPU info: {e}")
            return None
    
    async def _get_deployment_targets_status(self) -> List[Dict[str, Any]]:
        """Get status of deployment targets"""
        results = []
        
        for target in self.deployment_targets:
            try:
                # For local testing, just use a mock status
                # In production, you would make SSH or API calls to get real status
                
                # Mock data for now
                target_status = {
                    "host": target.get("host", "unknown"),
                    "status": "active",
                    "load": 0.3,  # Mock CPU load (0-1)
                    "specs": target.get("specs", "Unknown")
                }
                
                results.append(target_status)
            
            except Exception as e:
                logger.error(f"Error getting status for target {target.get('host', 'unknown')}: {e}")
                results.append({
                    "host": target.get("host", "unknown"),
                    "status": "unknown",
                    "load": 0,
                    "specs": "Error fetching target details"
                })
        
        return results

# Singleton instance
system_monitor = SystemMonitor()
