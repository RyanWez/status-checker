"""
User Management Service for role-based access control
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
from utils.timezone import myanmar_now

logger = logging.getLogger(__name__)

class UserRole(Enum):
    """User roles with different permission levels"""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

class UserPermissions:
    """Define permissions for each role"""
    
    ROLE_PERMISSIONS = {
        UserRole.ADMIN: {
            'add_domains': True,
            'remove_domains': True,
            'check_domains': True,
            'list_domains': True,
            'manage_users': True,
            'view_all_groups': True,
            'create_groups': True,
            'delete_groups': True,
            'bulk_operations': True,
            'system_settings': True
        },
        UserRole.USER: {
            'add_domains': False,
            'remove_domains': False,
            'check_domains': True,
            'list_domains': True,
            'manage_users': False,
            'view_all_groups': True,
            'create_groups': False,
            'delete_groups': False,
            'bulk_operations': False,
            'system_settings': False
        },
        UserRole.GUEST: {
            'add_domains': False,
            'remove_domains': False,
            'check_domains': True,
            'list_domains': True,
            'manage_users': False,
            'view_all_groups': False,  # Can only view assigned groups
            'create_groups': False,
            'delete_groups': False,
            'bulk_operations': False,
            'system_settings': False
        }
    }
    
    @classmethod
    def has_permission(cls, role: UserRole, permission: str) -> bool:
        """Check if a role has a specific permission"""
        return cls.ROLE_PERMISSIONS.get(role, {}).get(permission, False)

class UserManagementService:
    """Handles user management and role-based access control"""
    
    def __init__(self, db_service):
        self.db_service = db_service
        self.users_collection = db_service.db.users
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Create database indexes for better performance"""
        try:
            self.users_collection.create_index("user_id", unique=True)
            self.users_collection.create_index("username")
            self.users_collection.create_index("role")
        except Exception as e:
            logger.error(f"Error creating user indexes: {e}")
    
    def add_user(self, user_id: int, username: str, role: UserRole = UserRole.USER, 
                 added_by: int = None, allowed_groups: List[str] = None) -> bool:
        """Add a new user with specified role"""
        try:
            # Check if user already exists
            if self.get_user(user_id):
                return False
            
            user_doc = {
                'user_id': user_id,
                'username': username,
                'role': role.value,
                'added_at': myanmar_now(),
                'added_by': added_by,
                'allowed_groups': allowed_groups or [],
                'is_active': True,
                'last_activity': None
            }
            
            self.users_collection.insert_one(user_doc)
            logger.info(f"Added user {username} ({user_id}) with role {role.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding user {user_id}: {e}")
            return False
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user information by user ID"""
        try:
            return self.users_collection.find_one({'user_id': user_id})
        except Exception as e:
            logger.error(f"Error fetching user {user_id}: {e}")
            return None
    
    def get_user_role(self, user_id: int) -> UserRole:
        """Get user role, default to GUEST if not found"""
        user = self.get_user(user_id)
        if not user:
            return UserRole.GUEST
        
        try:
            return UserRole(user.get('role', UserRole.GUEST.value))
        except ValueError:
            return UserRole.GUEST
    
    def update_user_role(self, user_id: int, new_role: UserRole, updated_by: int) -> bool:
        """Update user role"""
        try:
            result = self.users_collection.update_one(
                {'user_id': user_id},
                {
                    '$set': {
                        'role': new_role.value,
                        'updated_at': myanmar_now(),
                        'updated_by': updated_by
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated user {user_id} role to {new_role.value}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error updating user role {user_id}: {e}")
            return False
    
    def remove_user(self, user_id: int, removed_by: int) -> bool:
        """Remove user from system"""
        try:
            result = self.users_collection.delete_one({'user_id': user_id})
            
            if result.deleted_count > 0:
                logger.info(f"Removed user {user_id} by admin {removed_by}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error removing user {user_id}: {e}")
            return False
    
    def get_all_users(self) -> List[Dict]:
        """Get all users"""
        try:
            return list(self.users_collection.find().sort('added_at', -1))
        except Exception as e:
            logger.error(f"Error fetching all users: {e}")
            return []
    
    def update_user_activity(self, user_id: int):
        """Update user's last activity timestamp"""
        try:
            self.users_collection.update_one(
                {'user_id': user_id},
                {'$set': {'last_activity': myanmar_now()}}
            )
        except Exception as e:
            logger.debug(f"Error updating user activity {user_id}: {e}")
    
    def has_permission(self, user_id: int, permission: str) -> bool:
        """Check if user has specific permission"""
        role = self.get_user_role(user_id)
        return UserPermissions.has_permission(role, permission)
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return self.get_user_role(user_id) == UserRole.ADMIN
    
    def can_access_group(self, user_id: int, group_name: str) -> bool:
        """Check if user can access specific group"""
        user = self.get_user(user_id)
        if not user:
            return False
        
        role = UserRole(user.get('role', UserRole.GUEST.value))
        
        # Admins can access all groups
        if role == UserRole.ADMIN:
            return True
        
        # Users can access all groups
        if role == UserRole.USER:
            return True
        
        # Guests can only access allowed groups
        if role == UserRole.GUEST:
            allowed_groups = user.get('allowed_groups', [])
            return group_name in allowed_groups
        
        return False
    
    def get_accessible_groups(self, user_id: int) -> List[str]:
        """Get list of groups user can access"""
        user = self.get_user(user_id)
        if not user:
            return []
        
        role = UserRole(user.get('role', UserRole.GUEST.value))
        
        # Admins and Users can access all groups
        if role in [UserRole.ADMIN, UserRole.USER]:
            # Return all groups from database
            return self.db_service.get_groups()
        
        # Guests can only access allowed groups
        if role == UserRole.GUEST:
            return user.get('allowed_groups', [])
        
        return []
    
    def add_user_to_group(self, user_id: int, group_name: str, added_by: int) -> bool:
        """Add user to allowed groups (for guests)"""
        try:
            result = self.users_collection.update_one(
                {'user_id': user_id},
                {
                    '$addToSet': {'allowed_groups': group_name},
                    '$set': {
                        'updated_at': myanmar_now(),
                        'updated_by': added_by
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Added user {user_id} to group {group_name}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error adding user {user_id} to group {group_name}: {e}")
            return False
    
    def remove_user_from_group(self, user_id: int, group_name: str, removed_by: int) -> bool:
        """Remove user from allowed groups"""
        try:
            result = self.users_collection.update_one(
                {'user_id': user_id},
                {
                    '$pull': {'allowed_groups': group_name},
                    '$set': {
                        'updated_at': myanmar_now(),
                        'updated_by': removed_by
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Removed user {user_id} from group {group_name}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error removing user {user_id} from group {group_name}: {e}")
            return False