"""
Simple health check server for Fly.io monitoring
"""
import asyncio
import json
import logging
from datetime import datetime
from aiohttp import web
from aiohttp.web import Application, Response
import threading

logger = logging.getLogger(__name__)

class HealthServer:
    """Simple HTTP server for health checks and basic metrics"""
    
    def __init__(self, port: int = 8080):
        self.port = port
        self.app = None
        self.runner = None
        self.site = None
        self.start_time = datetime.now()
        self.bot_status = "starting"
        
    async def health_handler(self, request):
        """Health check endpoint"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        health_data = {
            "status": "healthy" if self.bot_status == "running" else "unhealthy",
            "bot_status": self.bot_status,
            "uptime_seconds": uptime,
            "timestamp": datetime.now().isoformat()
        }
        
        status_code = 200 if self.bot_status == "running" else 503
        return web.json_response(health_data, status=status_code)
    
    async def metrics_handler(self, request):
        """Basic metrics endpoint"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        metrics = f"""# HELP bot_uptime_seconds Bot uptime in seconds
# TYPE bot_uptime_seconds counter
bot_uptime_seconds {uptime}

# HELP bot_status Bot status (1=running, 0=not running)
# TYPE bot_status gauge
bot_status {1 if self.bot_status == "running" else 0}
"""
        return Response(text=metrics, content_type="text/plain")
    
    async def start_server(self):
        """Start the health check server"""
        try:
            self.app = Application()
            self.app.router.add_get('/health', self.health_handler)
            self.app.router.add_get('/metrics', self.metrics_handler)
            self.app.router.add_get('/', self.health_handler)  # Root endpoint
            
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            
            self.site = web.TCPSite(self.runner, '0.0.0.0', self.port)
            await self.site.start()
            
            logger.info(f"Health server started on port {self.port}")
            
        except Exception as e:
            logger.error(f"Failed to start health server: {e}")
            raise
    
    async def stop_server(self):
        """Stop the health check server"""
        try:
            if self.site:
                await self.site.stop()
            if self.runner:
                await self.runner.cleanup()
            logger.info("Health server stopped")
        except Exception as e:
            logger.error(f"Error stopping health server: {e}")
    
    def set_bot_status(self, status: str):
        """Update bot status"""
        self.bot_status = status
        logger.debug(f"Bot status updated to: {status}")

# Global health server instance
health_server = HealthServer()