#!/usr/bin/env python3
"""
Test script for notification system
"""
import asyncio
import logging
from services.database import DatabaseService
from services.user_management import UserManagementService, UserRole
from config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_notification_recipients():
    """Test who receives notifications"""
    try:
        # Initialize services
        db_service = DatabaseService(settings.MONGO_URL)
        user_service = UserManagementService(db_service)
        
        logger.info("Testing Notification Recipients...")
        
        # Add test users
        test_users = [
            (111111111, "test_admin", UserRole.ADMIN),
            (222222222, "test_user", UserRole.USER),
            (333333333, "test_guest", UserRole.GUEST),
        ]
        
        for user_id, username, role in test_users:
            user_service.add_user(user_id, username, role)
            logger.info(f"Added test user: {username} ({role.value})")
        
        # Simulate getting notification recipients
        all_users = []
        
        # Add legacy admins from settings
        all_users.extend(settings.ADMIN_CHAT_IDS)
        logger.info(f"Legacy admins from settings: {settings.ADMIN_CHAT_IDS}")
        
        # Add registered users from database
        registered_users = user_service.get_all_users()
        for user in registered_users:
            user_id = user.get('user_id')
            if user_id and user_id not in all_users:
                all_users.append(user_id)
        
        logger.info(f"All notification recipients: {all_users}")
        logger.info(f"Total recipients: {len(all_users)}")
        
        # Show breakdown
        logger.info("\n=== Notification Recipients Breakdown ===")
        logger.info(f"Legacy Admins: {len(settings.ADMIN_CHAT_IDS)}")
        logger.info(f"Registered Users: {len(registered_users)}")
        logger.info(f"Total Unique Recipients: {len(all_users)}")
        
        # Show user roles who will receive notifications
        logger.info("\n=== Recipients by Role ===")
        for user in registered_users:
            user_id = user.get('user_id')
            username = user.get('username', 'Unknown')
            role = user.get('role', 'unknown')
            logger.info(f"• {username} ({user_id}) - {role.title()}")
        
        # Clean up test users
        for user_id, username, role in test_users:
            user_service.remove_user(user_id, 111111111)
        
        logger.info("\n✅ Notification recipients test completed!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
    finally:
        if 'db_service' in locals():
            db_service.close()

if __name__ == "__main__":
    asyncio.run(test_notification_recipients())