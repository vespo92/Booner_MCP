import os
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the app from app_with_websockets
logger.info("Importing app from app_with_websockets")
from api.app_with_websockets import app

# If this file is run directly
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting server with WebSocket support")
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
