"""
Configuration settings for the Telegram Domain Checker Bot
"""
import os
import logging
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class Settings:
    """Application settings loaded from environment variables"""
    
    def __init__(self):
        self.TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
        self.ADMIN_CHAT_IDS_STR = os.getenv('ADMIN_CHAT_IDS')
        self.MONGO_URL = os.getenv('MONGO_URL')
        
        # Parse admin chat IDs
        self.ADMIN_CHAT_IDS = self._parse_admin_chat_ids()
        
        # Validate required settings
        self._validate_settings()
    
    def _parse_admin_chat_ids(self) -> List[int]:
        """Parse admin chat IDs from environment variable"""
        admin_ids = []
        if self.ADMIN_CHAT_IDS_STR:
            try:
                admin_ids = [int(id.strip()) for id in self.ADMIN_CHAT_IDS_STR.split(',')]
            except ValueError:
                logger.error("Invalid ADMIN_CHAT_IDS format. Use comma-separated numbers.")
        return admin_ids
    
    def _validate_settings(self):
        """Validate that all required settings are present"""
        if not self.TELEGRAM_TOKEN:
            raise ValueError("TELEGRAM_TOKEN is required")
        if not self.ADMIN_CHAT_IDS:
            raise ValueError("ADMIN_CHAT_IDS is required")
        if not self.MONGO_URL:
            raise ValueError("MONGO_URL is required")
    
    @property
    def is_admin(self) -> callable:
        """Return a function to check if user is admin"""
        def check_admin(user_id: int) -> bool:
            return user_id in self.ADMIN_CHAT_IDS
        return check_admin

# Global settings instance
settings = Settings()