#!/usr/bin/env python3
"""
Test script to verify permission system for domain operations
"""
import asyncio
import logging
from services.database import DatabaseService
from services.user_management import UserManagementService, UserRole
from config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_permissions():
    """Test permission system"""
    try:
        # Initialize services
        db_service = DatabaseService(settings.MONGO_URL)
        user_service = UserManagementService(db_service)
        
        logger.info("Testing Permission System...")
        
        # Test user IDs
        admin_id = 111111111
        user_id = 222222222
        guest_id = 333333333
        
        # Add test users
        user_service.add_user(admin_id, "test_admin", UserRole.ADMIN)
        user_service.add_user(user_id, "test_user", UserRole.USER)
        user_service.add_user(guest_id, "test_guest", UserRole.GUEST)
        
        # Test permissions
        permissions_to_test = [
            'add_domains',
            'remove_domains',
            'check_domains',
            'list_domains',
            'manage_users'
        ]
        
        logger.info("\n=== Permission Test Results ===")
        logger.info(f"{'Permission':<15} {'Admin':<8} {'User':<8} {'Guest':<8}")
        logger.info("-" * 45)
        
        for permission in permissions_to_test:
            admin_can = user_service.has_permission(admin_id, permission)
            user_can = user_service.has_permission(user_id, permission)
            guest_can = user_service.has_permission(guest_id, permission)
            
            logger.info(f"{permission:<15} {'✅' if admin_can else '❌':<8} {'✅' if user_can else '❌':<8} {'✅' if guest_can else '❌':<8}")
        
        # Test specific scenarios
        logger.info("\n=== Specific Test Cases ===")
        
        # Admin should be able to add/remove domains
        logger.info(f"Admin can add domains: {'✅' if user_service.has_permission(admin_id, 'add_domains') else '❌'}")
        logger.info(f"Admin can remove domains: {'✅' if user_service.has_permission(admin_id, 'remove_domains') else '❌'}")
        
        # User should NOT be able to add/remove domains
        logger.info(f"User can add domains: {'❌' if not user_service.has_permission(user_id, 'add_domains') else '⚠️ SHOULD BE NO'}")
        logger.info(f"User can remove domains: {'❌' if not user_service.has_permission(user_id, 'remove_domains') else '⚠️ SHOULD BE NO'}")
        
        # Guest should NOT be able to add/remove domains
        logger.info(f"Guest can add domains: {'❌' if not user_service.has_permission(guest_id, 'add_domains') else '⚠️ SHOULD BE NO'}")
        logger.info(f"Guest can remove domains: {'❌' if not user_service.has_permission(guest_id, 'remove_domains') else '⚠️ SHOULD BE NO'}")
        
        # All should be able to check and list domains
        logger.info(f"All can check domains: {'✅' if all([user_service.has_permission(uid, 'check_domains') for uid in [admin_id, user_id, guest_id]]) else '❌'}")
        logger.info(f"All can list domains: {'✅' if all([user_service.has_permission(uid, 'list_domains') for uid in [admin_id, user_id, guest_id]]) else '❌'}")
        
        # Clean up test users
        user_service.remove_user(admin_id, admin_id)
        user_service.remove_user(user_id, admin_id)
        user_service.remove_user(guest_id, admin_id)
        
        logger.info("\n✅ Permission system test completed!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
    finally:
        if 'db_service' in locals():
            db_service.close()

if __name__ == "__main__":
    asyncio.run(test_permissions())