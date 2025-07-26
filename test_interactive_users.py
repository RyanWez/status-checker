#!/usr/bin/env python3
"""
Test script for interactive user management features
"""
import asyncio
import logging
from services.database import DatabaseService
from services.user_management import UserManagementService, UserRole
from handlers.user_management import UserManagementHandlers
from config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_interactive_users():
    """Test interactive user management"""
    try:
        # Initialize services
        db_service = DatabaseService(settings.MONGO_URL)
        user_service = UserManagementService(db_service)
        user_handlers = UserManagementHandlers(db_service, user_service)
        
        logger.info("Testing Interactive User Management...")
        
        # Add test users
        test_users = [
            (111111111, "test_admin", UserRole.ADMIN),
            (222222222, "test_user", UserRole.USER),
            (333333333, "test_guest", UserRole.GUEST),
            (444444444, "another_user", UserRole.USER),
            (555555555, "another_guest", UserRole.GUEST),
        ]
        
        for user_id, username, role in test_users:
            user_service.add_user(user_id, username, role)
            logger.info(f"Added test user: {username} ({role.value})")
        
        # Test user listing
        users = user_service.get_all_users()
        logger.info(f"\nTotal users in system: {len(users)}")
        
        # Test pagination logic
        USERS_PER_PAGE = 5
        total_pages = (len(users) - 1) // USERS_PER_PAGE + 1
        logger.info(f"Total pages needed: {total_pages}")
        
        # Test role changes
        logger.info("\nTesting role changes...")
        
        # Change user role
        success = user_service.update_user_role(222222222, UserRole.ADMIN, 111111111)
        logger.info(f"Role change test: {'✅' if success else '❌'}")
        
        # Test permissions after role change
        can_manage = user_service.has_permission(222222222, 'manage_users')
        logger.info(f"New admin can manage users: {'✅' if can_manage else '❌'}")
        
        # Test user removal
        logger.info("\nTesting user removal...")
        
        # Remove a test user
        success = user_service.remove_user(555555555, 111111111)
        logger.info(f"User removal test: {'✅' if success else '❌'}")
        
        # Verify user is gone
        removed_user = user_service.get_user(555555555)
        logger.info(f"User properly removed: {'✅' if not removed_user else '❌'}")
        
        # Test callback data generation
        logger.info("\nTesting callback data patterns...")
        
        test_callbacks = [
            "users_page_0",
            "users_page_1", 
            "user_info_123456789",
            "user_delete_confirm_123456789",
            "user_delete_123456789",
            "user_change_role_123456789",
            "set_role_123456789_admin"
        ]
        
        for callback in test_callbacks:
            if callback.startswith("users_page_"):
                page = int(callback.split("_")[-1])
                logger.info(f"Page callback: {callback} -> page {page}")
            elif callback.startswith("user_info_"):
                user_id = callback.replace("user_info_", "")
                logger.info(f"User info callback: {callback} -> user {user_id}")
            elif callback.startswith("set_role_"):
                parts = callback.split("_")
                user_id = parts[2]
                role = parts[3]
                logger.info(f"Role change callback: {callback} -> user {user_id}, role {role}")
        
        # Clean up test users
        logger.info("\nCleaning up test users...")
        for user_id, username, role in test_users:
            if user_id != 555555555:  # Already removed
                user_service.remove_user(user_id, 111111111)
        
        logger.info("✅ Interactive user management test completed!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
    finally:
        if 'db_service' in locals():
            db_service.close()

if __name__ == "__main__":
    asyncio.run(test_interactive_users())