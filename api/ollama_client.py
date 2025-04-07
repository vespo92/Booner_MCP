import aiohttp
import json
import logging
from typing import Dict, List, Optional, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OllamaClient:
    """Client for interacting with the Ollama API for LLM inference."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        """
        Initialize the Ollama client.
        
        Args:
            base_url: Base URL for the Ollama API
        """
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List all available models from Ollama."""
        async with self.session.get(f"{self.base_url}/api/tags") as response:
            response.raise_for_status()
            result = await response.json()
            return result.get("models", [])
    
    async def generate(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Generate text using the specified model.
        
        Args:
            model: The name of the model to use
            prompt: The prompt to send to the model
            system: Optional system message
            temperature: Controls randomness (0.0-1.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            
        Returns:
            The model's response
        """
        data = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "num_predict": max_tokens,
            "stream": stream
        }
        
        if system:
            data["system"] = system
        
        if stream:
            return await self._stream_response(data)
        else:
            return await self._complete_response(data)
    
    async def _complete_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get a complete response from the model."""
        async with self.session.post(f"{self.base_url}/api/generate", json=data) as response:
            response.raise_for_status()
            return await response.json()
    
    async def _stream_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Stream the response from the model."""
        response_text = ""
        async with self.session.post(f"{self.base_url}/api/generate", json=data) as response:
            response.raise_for_status()
            async for line in response.content:
                if not line:
                    continue
                
                chunk = json.loads(line)
                if "response" in chunk:
                    response_text += chunk["response"]
                
                if chunk.get("done", False):
                    return {
                        "model": chunk.get("model", data["model"]),
                        "response": response_text,
                        "done": True
                    }
        
        return {"response": response_text, "done": False}

async def test_ollama():
    """Test the Ollama client."""
    async with OllamaClient() as client:
        try:
            models = await client.list_models()
            logger.info(f"Available models: {models}")
            
            # Test generation
            if models:
                # Use the first available model
                model_name = models[0]["name"]
                logger.info(f"Testing generation with model: {model_name}")
                
                response = await client.generate(
                    model=model_name,
                    prompt="Hello, I am an AI agent. Can you tell me about the Model Context Protocol?",
                    temperature=0.7,
                    max_tokens=500
                )
                
                logger.info(f"Response: {response['response']}")
                
        except Exception as e:
            logger.error(f"Error communicating with Ollama: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_ollama())
