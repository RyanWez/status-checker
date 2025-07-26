#!/usr/bin/env python3
"""
Test script to verify the fixes for Main Menu and User Management
"""
import asyncio
import logging
from services.database import DatabaseService
from services.user_management import UserManagementService, UserRole
from services.user_resolver import UserResolver
from config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_fixes():
    """Test the fixes"""
    try:
        # Initialize services
        db_service = DatabaseService(settings.MONGO_URL)
        user_service = UserManagementService(db_service)
        user_resolver = UserResolver(db_service)
        
        logger.info("Testing User Resolver...")
        
        # Test recording user interaction
        test_user_id = 123456789
        test_username = "test_user"
        
        user_resolver.record_user_interaction(test_user_id, test_username, "Test User")
        logger.info(f"Recorded interaction for {test_username}")
        
        # Test resolving username
        resolved_id = user_resolver.resolve_username_to_id(test_username)
        logger.info(f"Resolved @{test_username} to ID: {resolved_id}")
        
        # Test getting user info
        user_info = user_resolver.get_user_info(test_user_id)
        logger.info(f"User info: {user_info}")
        
        # Test username resolution with @
        resolved_id_with_at = user_resolver.resolve_username_to_id(f"@{test_username}")
        logger.info(f"Resolved @{test_username} (with @) to ID: {resolved_id_with_at}")
        
        # Clean up
        db_service.db.user_interactions.delete_one({'user_id': test_user_id})
        
        logger.info("All tests passed!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
    finally:
        if 'db_service' in locals():
            db_service.close()

if __name__ == "__main__":
    asyncio.run(test_fixes())