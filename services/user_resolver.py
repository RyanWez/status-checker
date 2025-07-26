"""
User ID Resolution Service
Helps resolve usernames to user IDs and manage user interactions
"""
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class UserResolver:
    """Service to help resolve usernames to user IDs"""
    
    def __init__(self, db_service):
        self.db_service = db_service
        self.interaction_cache = {}  # In-memory cache for recent interactions
    
    def record_user_interaction(self, user_id: int, username: str = None, first_name: str = None):
        """Record user interaction for future username resolution"""
        try:
            # Store in cache
            self.interaction_cache[user_id] = {
                'username': username,
                'first_name': first_name,
                'last_seen': datetime.now()
            }
            
            # Also store in database for persistence
            self.db_service.db.user_interactions.update_one(
                {'user_id': user_id},
                {
                    '$set': {
                        'user_id': user_id,
                        'username': username,
                        'first_name': first_name,
                        'last_seen': datetime.now()
                    }
                },
                upsert=True
            )
            
        except Exception as e:
            logger.error(f"Error recording user interaction: {e}")
    
    def resolve_username_to_id(self, username: str) -> Optional[int]:
        """Try to resolve username to user ID from recent interactions"""
        try:
            # Remove @ if present
            clean_username = username.lstrip('@').lower()
            
            # Check cache first
            for user_id, data in self.interaction_cache.items():
                if data.get('username', '').lower() == clean_username:
                    return user_id
            
            # Check database
            result = self.db_service.db.user_interactions.find_one(
                {'username': {'$regex': f'^{clean_username}$', '$options': 'i'}}
            )
            
            if result:
                return result['user_id']
            
            return None
            
        except Exception as e:
            logger.error(f"Error resolving username {username}: {e}")
            return None
    
    def get_user_info(self, user_id: int) -> Optional[Dict]:
        """Get cached user information"""
        try:
            # Check cache first
            if user_id in self.interaction_cache:
                return self.interaction_cache[user_id]
            
            # Check database
            result = self.db_service.db.user_interactions.find_one({'user_id': user_id})
            if result:
                # Update cache
                self.interaction_cache[user_id] = {
                    'username': result.get('username'),
                    'first_name': result.get('first_name'),
                    'last_seen': result.get('last_seen')
                }
                return self.interaction_cache[user_id]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user info for {user_id}: {e}")
            return None
    
    def cleanup_old_interactions(self, days: int = 30):
        """Clean up old interaction records"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Clean cache
            to_remove = []
            for user_id, data in self.interaction_cache.items():
                if data.get('last_seen', datetime.min) < cutoff_date:
                    to_remove.append(user_id)
            
            for user_id in to_remove:
                del self.interaction_cache[user_id]
            
            # Clean database
            self.db_service.db.user_interactions.delete_many(
                {'last_seen': {'$lt': cutoff_date}}
            )
            
            logger.info(f"Cleaned up {len(to_remove)} old user interactions")
            
        except Exception as e:
            logger.error(f"Error cleaning up interactions: {e}")
    
    def suggest_user_id_methods(self, username: str) -> str:
        """Generate helpful message for getting user ID"""
        return (
            f"**How to get User ID for @{username}:**\n\n"
            f"**Method 1: Ask user to interact with bot**\n"
            f"• User sends `/start` to this bot\n"
            f"• Bot will log their User ID\n"
            f"• Then use: `/adduser <user_id> {username} <role>`\n\n"
            f"**Method 2: Use @userinfobot**\n"
            f"• User forwards any message to @userinfobot\n"
            f"• Bot replies with User ID\n"
            f"• Provide ID to admin\n\n"
            f"**Method 3: Use @username_to_id_bot**\n"
            f"• Send @{username} to @username_to_id_bot\n"
            f"• Bot replies with User ID (if public)\n\n"
            f"**Method 4: Check recent interactions**\n"
            f"• If user recently used this bot, ID might be cached\n"
            f"• Use `/finduser @{username}` to check"
        )