#!/usr/bin/env python3
"""
Test script for User Management System
"""
import asyncio
import logging
from services.database import DatabaseService
from services.user_management import UserManagementService, UserRole
from config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_user_management():
    """Test user management functionality"""
    try:
        # Initialize services
        db_service = DatabaseService(settings.MONGO_URL)
        user_service = UserManagementService(db_service)
        
        logger.info("Testing User Management System...")
        
        # Test adding users
        logger.info("1. Testing user addition...")
        
        # Add admin user
        result1 = user_service.add_user(123456789, "test_admin", UserRole.ADMIN)
        logger.info(f"Add admin user: {result1}")
        
        # Add regular user
        result2 = user_service.add_user(987654321, "test_user", UserRole.USER)
        logger.info(f"Add regular user: {result2}")
        
        # Add guest user
        result3 = user_service.add_user(555666777, "test_guest", UserRole.GUEST, allowed_groups=["Web1", "Web2"])
        logger.info(f"Add guest user: {result3}")
        
        # Test permissions
        logger.info("2. Testing permissions...")
        
        admin_can_add = user_service.has_permission(123456789, 'add_domains')
        user_can_add = user_service.has_permission(987654321, 'add_domains')
        guest_can_add = user_service.has_permission(555666777, 'add_domains')
        
        logger.info(f"Admin can add domains: {admin_can_add}")
        logger.info(f"User can add domains: {user_can_add}")
        logger.info(f"Guest can add domains: {guest_can_add}")
        
        # Test group access
        logger.info("3. Testing group access...")
        
        admin_groups = user_service.get_accessible_groups(123456789)
        user_groups = user_service.get_accessible_groups(987654321)
        guest_groups = user_service.get_accessible_groups(555666777)
        
        logger.info(f"Admin accessible groups: {admin_groups}")
        logger.info(f"User accessible groups: {user_groups}")
        logger.info(f"Guest accessible groups: {guest_groups}")
        
        # Test user listing
        logger.info("4. Testing user listing...")
        all_users = user_service.get_all_users()
        logger.info(f"Total users: {len(all_users)}")
        
        for user in all_users:
            logger.info(f"User: {user['username']} ({user['user_id']}) - Role: {user['role']}")
        
        # Clean up test users
        logger.info("5. Cleaning up test users...")
        user_service.remove_user(123456789, 123456789)
        user_service.remove_user(987654321, 123456789)
        user_service.remove_user(555666777, 123456789)
        
        logger.info("User management test completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
    finally:
        if 'db_service' in locals():
            db_service.close()

if __name__ == "__main__":
    asyncio.run(test_user_management())