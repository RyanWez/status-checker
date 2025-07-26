"""
User Management Handlers for Telegram Bot
"""
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.user_management import UserManagementService, UserRole
from services.user_resolver import UserResolver

logger = logging.getLogger(__name__)

class UserManagementHandlers:
    """Handles user management commands and interactions"""
    
    def __init__(self, db_service, user_service: UserManagementService):
        self.db_service = db_service
        self.user_service = user_service
        self.user_resolver = UserResolver(db_service)
    
    async def add_user_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /adduser command (Admin only)"""
        user_id = update.effective_user.id
        
        # Check if user is admin
        if not self.user_service.is_admin(user_id):
            await update.message.reply_text(
                "❌ **Access Denied**\n\n"
                "Only administrators can add users.",
                parse_mode='Markdown'
            )
            return
        
        # Parse command arguments
        args = context.args
        if len(args) < 2:
            await update.message.reply_text(
                "📝 **Add User Usage**\n\n"
                "**Format:** `/adduser <user_id> <username> [role]`\n\n"
                "**Roles:**\n"
                "• `admin` - Full access\n"
                "• `user` - Read-only access (default)\n"
                "• `guest` - Limited group access\n\n"
                "**Examples:**\n"
                "• `/adduser 123456789 john_doe user`\n"
                "• `/adduser 987654321 jane_admin admin`",
                parse_mode='Markdown'
            )
            return
        
        try:
            # Handle both user ID and username formats
            user_identifier = args[0].strip()
            
            # Check if first argument is username (starts with @) or user ID
            if user_identifier.startswith('@'):
                # Username format: /adduser @username role
                target_username = user_identifier[1:]  # Remove @
                role_str = args[1] if len(args) > 1 else 'user'
                
                # Try to resolve username to user ID
                target_user_id = self.user_resolver.resolve_username_to_id(target_username)
                
                if target_user_id is None:
                    # Username not found in recent interactions
                    help_text = (
                        f"❌ **Username @{target_username} Not Found**\n\n"
                        f"The username @{target_username} hasn't interacted with this bot recently.\n\n"
                        f"{self.user_resolver.suggest_user_id_methods(target_username)}"
                    )
                    
                    await update.message.reply_text(help_text, parse_mode='Markdown')
                    return
                
                # Use resolved user ID and username
                username = target_username
                
            else:
                # User ID format: /adduser user_id username role
                target_user_id = int(user_identifier)
                username = args[1].strip() if len(args) > 1 else f"user_{target_user_id}"
                role_str = args[2] if len(args) > 2 else 'user'
            
            # Validate role
            try:
                role = UserRole(role_str.lower())
            except ValueError:
                await update.message.reply_text(
                    "❌ **Invalid Role**\n\n"
                    "Valid roles: `admin`, `user`, `guest`",
                    parse_mode='Markdown'
                )
                return
            
            # Add user
            if self.user_service.add_user(target_user_id, username, role, user_id):
                await update.message.reply_text(
                    f"✅ **User Added Successfully**\n\n"
                    f"**User ID:** `{target_user_id}`\n"
                    f"**Username:** @{username}\n"
                    f"**Role:** {role.value.title()}\n\n"
                    f"User can now access the bot with {role.value} permissions.",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    "❌ **Failed to Add User**\n\n"
                    "User may already exist in the system.",
                    parse_mode='Markdown'
                )
                
        except ValueError:
            await update.message.reply_text(
                "❌ **Invalid User ID**\n\n"
                "User ID must be a number.",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error in add_user_command: {e}")
            await update.message.reply_text(
                "❌ **Error**\n\n"
                "Failed to add user. Please try again.",
                parse_mode='Markdown'
            )
    
    async def remove_user_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /removeuser command (Admin only)"""
        user_id = update.effective_user.id
        
        # Check if user is admin
        if not self.user_service.is_admin(user_id):
            await update.message.reply_text(
                "❌ **Access Denied**\n\n"
                "Only administrators can remove users.",
                parse_mode='Markdown'
            )
            return
        
        # Parse command arguments
        args = context.args
        if len(args) < 1:
            await update.message.reply_text(
                "📝 **Remove User Usage**\n\n"
                "**Format:** `/removeuser <user_id>`\n\n"
                "**Example:**\n"
                "• `/removeuser 123456789`",
                parse_mode='Markdown'
            )
            return
        
        try:
            target_user_id = int(args[0])
            
            # Don't allow removing self
            if target_user_id == user_id:
                await update.message.reply_text(
                    "❌ **Cannot Remove Self**\n\n"
                    "You cannot remove your own account.",
                    parse_mode='Markdown'
                )
                return
            
            # Get user info before removal
            target_user = self.user_service.get_user(target_user_id)
            if not target_user:
                await update.message.reply_text(
                    "❌ **User Not Found**\n\n"
                    f"User ID `{target_user_id}` is not in the system.",
                    parse_mode='Markdown'
                )
                return
            
            # Remove user
            if self.user_service.remove_user(target_user_id, user_id):
                await update.message.reply_text(
                    f"✅ **User Removed Successfully**\n\n"
                    f"**User ID:** `{target_user_id}`\n"
                    f"**Username:** @{target_user.get('username', 'Unknown')}\n"
                    f"**Role:** {target_user.get('role', 'unknown').title()}\n\n"
                    f"User no longer has access to the bot.",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    "❌ **Failed to Remove User**\n\n"
                    "Please try again.",
                    parse_mode='Markdown'
                )
                
        except ValueError:
            await update.message.reply_text(
                "❌ **Invalid User ID**\n\n"
                "User ID must be a number.",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error in remove_user_command: {e}")
            await update.message.reply_text(
                "❌ **Error**\n\n"
                "Failed to remove user. Please try again.",
                parse_mode='Markdown'
            )
    
    async def list_users_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /listusers command (Admin only)"""
        user_id = update.effective_user.id
        
        # Check if user is admin
        if not self.user_service.is_admin(user_id):
            await update.message.reply_text(
                "❌ **Access Denied**\n\n"
                "Only administrators can view user list.",
                parse_mode='Markdown'
            )
            return
        
        try:
            users = self.user_service.get_all_users()
            
            if not users:
                await update.message.reply_text(
                    "📋 **No Users Found**\n\n"
                    "No users are currently registered in the system.",
                    parse_mode='Markdown'
                )
                return
            
            # Format user list
            user_list = "👥 **Registered Users**\n\n"
            
            for user in users:
                role_emoji = {
                    'admin': '👑',
                    'user': '👤',
                    'guest': '👥'
                }.get(user.get('role', 'guest'), '❓')
                
                username = user.get('username', 'Unknown')
                user_id_str = user.get('user_id', 'Unknown')
                role = user.get('role', 'unknown').title()
                added_at = user.get('added_at')
                last_activity = user.get('last_activity')
                
                user_list += f"{role_emoji} **@{username}** (`{user_id_str}`)\n"
                user_list += f"   • Role: {role}\n"
                
                if added_at:
                    user_list += f"   • Added: {added_at.strftime('%Y-%m-%d %H:%M')}\n"
                
                if last_activity:
                    user_list += f"   • Last seen: {last_activity.strftime('%Y-%m-%d %H:%M')}\n"
                
                # Show allowed groups for guests
                if user.get('role') == 'guest':
                    allowed_groups = user.get('allowed_groups', [])
                    if allowed_groups:
                        user_list += f"   • Groups: {', '.join(allowed_groups)}\n"
                
                user_list += "\n"
            
            # Split message if too long
            if len(user_list) > 4000:
                # Send in chunks
                chunks = [user_list[i:i+4000] for i in range(0, len(user_list), 4000)]
                for i, chunk in enumerate(chunks):
                    if i == 0:
                        await update.message.reply_text(chunk, parse_mode='Markdown')
                    else:
                        await update.message.reply_text(f"**Continued...**\n\n{chunk}", parse_mode='Markdown')
            else:
                await update.message.reply_text(user_list, parse_mode='Markdown')
                
        except Exception as e:
            logger.error(f"Error in list_users_command: {e}")
            await update.message.reply_text(
                "❌ **Error**\n\n"
                "Failed to fetch user list. Please try again.",
                parse_mode='Markdown'
            )
    
    async def interactive_user_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
        """Show interactive user list with buttons (Admin only)"""
        user_id = update.effective_user.id
        
        # Check if user is admin
        if not self.user_service.is_admin(user_id):
            error_msg = "❌ **Access Denied**\n\nOnly administrators can view user list."
            if update.callback_query:
                await update.callback_query.answer(error_msg, show_alert=True)
            else:
                await update.message.reply_text(error_msg, parse_mode='Markdown')
            return
        
        try:
            users = self.user_service.get_all_users()
            
            if not users:
                text = "📋 **No Users Found**\n\nNo users are currently registered in the system."
                keyboard = [[InlineKeyboardButton("🔙 Back to User Management", callback_data="user_management")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                if update.callback_query:
                    await update.callback_query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
                else:
                    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)
                return
            
            # Pagination settings
            USERS_PER_PAGE = 5
            total_pages = (len(users) - 1) // USERS_PER_PAGE + 1
            start_idx = page * USERS_PER_PAGE
            end_idx = start_idx + USERS_PER_PAGE
            page_users = users[start_idx:end_idx]
            
            # Create header with timestamp to make refresh unique
            from datetime import datetime
            current_time = datetime.now().strftime('%H:%M:%S')
            
            text = f"👥 **User Management** (Page {page + 1}/{total_pages})\n"
            text += f"**Total Users:** {len(users)}\n"
            text += f"*Last updated: {current_time}*\n\n"
            
            # Create keyboard with user buttons
            keyboard = []
            
            for user in page_users:
                role_emoji = {
                    'admin': '👑',
                    'user': '👤', 
                    'guest': '👥'
                }.get(user.get('role', 'guest'), '❓')
                
                username = user.get('username', 'Unknown')
                user_id_str = user.get('user_id', 'Unknown')
                role = user.get('role', 'unknown').title()
                
                # User info button
                user_button_text = f"{role_emoji} @{username} ({role})"
                keyboard.append([
                    InlineKeyboardButton(user_button_text, callback_data=f"user_info_{user_id_str}"),
                    InlineKeyboardButton("🗑️", callback_data=f"user_delete_confirm_{user_id_str}")
                ])
            
            # Add pagination buttons
            nav_buttons = []
            if page > 0:
                nav_buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"users_page_{page-1}"))
            
            nav_buttons.append(InlineKeyboardButton(f"📄 {page+1}/{total_pages}", callback_data="noop"))
            
            if page < total_pages - 1:
                nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"users_page_{page+1}"))
            
            if nav_buttons:
                keyboard.append(nav_buttons)
            
            # Add action buttons
            keyboard.append([
                InlineKeyboardButton("➕ Add User", callback_data="admin_add_user_help"),
                InlineKeyboardButton("🔄 Refresh", callback_data=f"users_page_{page}")
            ])
            
            keyboard.append([
                InlineKeyboardButton("📊 User Stats", callback_data="admin_user_stats"),
                InlineKeyboardButton("🔙 Back", callback_data="user_management")
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if update.callback_query:
                try:
                    await update.callback_query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
                except Exception as e:
                    if "Message is not modified" in str(e):
                        await update.callback_query.answer("✅ User list is already up to date!")
                    else:
                        logger.error(f"Error editing user list message: {e}")
                        await update.callback_query.answer("❌ Failed to refresh user list")
            else:
                await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)
                
        except Exception as e:
            logger.error(f"Error in interactive_user_list: {e}")
            error_text = "❌ **Error**\n\nFailed to fetch user list. Please try again."
            
            if update.callback_query:
                await update.callback_query.edit_message_text(error_text, parse_mode='Markdown')
            else:
                await update.message.reply_text(error_text, parse_mode='Markdown')
    
    async def show_user_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE, target_user_id: str):
        """Show detailed information about a specific user"""
        user_id = update.effective_user.id
        
        # Check if user is admin
        if not self.user_service.is_admin(user_id):
            await update.callback_query.answer("❌ Access Denied", show_alert=True)
            return
        
        try:
            target_user = self.user_service.get_user(int(target_user_id))
            
            if not target_user:
                await update.callback_query.edit_message_text(
                    f"❌ **User Not Found**\n\nUser ID `{target_user_id}` not found in system.",
                    parse_mode='Markdown'
                )
                return
            
            role_emoji = {
                'admin': '👑',
                'user': '👤',
                'guest': '👥'
            }.get(target_user.get('role', 'guest'), '❓')
            
            username = target_user.get('username', 'Unknown')
            role = target_user.get('role', 'unknown').title()
            added_at = target_user.get('added_at')
            added_by = target_user.get('added_by')
            last_activity = target_user.get('last_activity')
            
            info_text = f"{role_emoji} **User Details**\n\n"
            info_text += f"**Username:** @{username}\n"
            info_text += f"**User ID:** `{target_user_id}`\n"
            info_text += f"**Role:** {role}\n"
            
            if added_at:
                info_text += f"**Added:** {added_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            if added_by:
                info_text += f"**Added By:** {added_by}\n"
            
            if last_activity:
                info_text += f"**Last Activity:** {last_activity.strftime('%Y-%m-%d %H:%M:%S')}\n"
            else:
                info_text += f"**Last Activity:** Never\n"
            
            # Show permissions
            info_text += f"\n**Permissions:**\n"
            permissions = {
                'check_domains': '🔍 Check domains',
                'list_domains': '📋 List domains', 
                'add_domains': '➕ Add domains',
                'remove_domains': '➖ Remove domains',
                'manage_users': '👥 Manage users',
                'bulk_operations': '📦 Bulk operations'
            }
            
            for perm, desc in permissions.items():
                has_perm = self.user_service.has_permission(int(target_user_id), perm)
                status = "✅" if has_perm else "❌"
                info_text += f"   {status} {desc}\n"
            
            # Show allowed groups for guests
            if target_user.get('role') == 'guest':
                allowed_groups = target_user.get('allowed_groups', [])
                info_text += f"\n**Allowed Groups:** {', '.join(allowed_groups) if allowed_groups else 'None'}\n"
            
            # Create action buttons
            keyboard = [
                [
                    InlineKeyboardButton("🔄 Change Role", callback_data=f"user_change_role_{target_user_id}"),
                    InlineKeyboardButton("🗑️ Remove User", callback_data=f"user_delete_confirm_{target_user_id}")
                ],
                [
                    InlineKeyboardButton("📋 Back to List", callback_data="users_page_0"),
                    InlineKeyboardButton("🔙 User Management", callback_data="user_management")
                ]
            ]
            
            # Don't allow removing self
            if int(target_user_id) == user_id:
                keyboard[0] = [InlineKeyboardButton("🔄 Change Role", callback_data=f"user_change_role_{target_user_id}")]
                info_text += f"\n⚠️ **Note:** You cannot remove your own account."
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                info_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error in show_user_details: {e}")
            await update.callback_query.edit_message_text(
                "❌ **Error**\n\nFailed to load user details.",
                parse_mode='Markdown'
            )
    
    async def confirm_user_deletion(self, update: Update, context: ContextTypes.DEFAULT_TYPE, target_user_id: str):
        """Show confirmation dialog for user deletion"""
        user_id = update.effective_user.id
        
        # Check if user is admin
        if not self.user_service.is_admin(user_id):
            await update.callback_query.answer("❌ Access Denied", show_alert=True)
            return
        
        # Don't allow removing self
        if int(target_user_id) == user_id:
            await update.callback_query.answer("❌ Cannot remove your own account", show_alert=True)
            return
        
        try:
            target_user = self.user_service.get_user(int(target_user_id))
            
            if not target_user:
                await update.callback_query.edit_message_text(
                    f"❌ **User Not Found**\n\nUser ID `{target_user_id}` not found.",
                    parse_mode='Markdown'
                )
                return
            
            username = target_user.get('username', 'Unknown')
            role = target_user.get('role', 'unknown').title()
            
            keyboard = [
                [
                    InlineKeyboardButton("✅ Yes, Remove", callback_data=f"user_delete_{target_user_id}"),
                    InlineKeyboardButton("❌ Cancel", callback_data=f"user_info_{target_user_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                f"🗑️ **Confirm User Removal**\n\n"
                f"Are you sure you want to remove this user?\n\n"
                f"**Username:** @{username}\n"
                f"**User ID:** `{target_user_id}`\n"
                f"**Role:** {role}\n\n"
                f"⚠️ **This action cannot be undone.**\n"
                f"The user will lose access to the bot immediately.",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error in confirm_user_deletion: {e}")
            await update.callback_query.edit_message_text(
                "❌ **Error**\n\nFailed to load user information.",
                parse_mode='Markdown'
            )
    
    async def delete_user_confirmed(self, update: Update, context: ContextTypes.DEFAULT_TYPE, target_user_id: str):
        """Actually delete the user after confirmation"""
        user_id = update.effective_user.id
        
        # Check if user is admin
        if not self.user_service.is_admin(user_id):
            await update.callback_query.answer("❌ Access Denied", show_alert=True)
            return
        
        # Don't allow removing self
        if int(target_user_id) == user_id:
            await update.callback_query.answer("❌ Cannot remove your own account", show_alert=True)
            return
        
        try:
            target_user = self.user_service.get_user(int(target_user_id))
            
            if not target_user:
                await update.callback_query.edit_message_text(
                    f"❌ **User Not Found**\n\nUser ID `{target_user_id}` not found.",
                    parse_mode='Markdown'
                )
                return
            
            username = target_user.get('username', 'Unknown')
            role = target_user.get('role', 'unknown').title()
            
            # Remove user
            if self.user_service.remove_user(int(target_user_id), user_id):
                await update.callback_query.edit_message_text(
                    f"✅ **User Removed Successfully**\n\n"
                    f"**Username:** @{username}\n"
                    f"**User ID:** `{target_user_id}`\n"
                    f"**Role:** {role}\n\n"
                    f"The user no longer has access to the bot.",
                    parse_mode='Markdown'
                )
                
                # Auto-redirect to user list after 2 seconds
                await asyncio.sleep(2)
                await self.interactive_user_list(update, context, 0)
            else:
                await update.callback_query.edit_message_text(
                    f"❌ **Failed to Remove User**\n\n"
                    f"Could not remove user `{target_user_id}`. Please try again.",
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            logger.error(f"Error in delete_user_confirmed: {e}")
            await update.callback_query.edit_message_text(
                "❌ **Error**\n\nFailed to remove user. Please try again.",
                parse_mode='Markdown'
            )
    
    async def user_info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /userinfo command"""
        user_id = update.effective_user.id
        user = self.user_service.get_user(user_id)
        
        if not user:
            await update.message.reply_text(
                "❌ **User Not Found**\n\n"
                "You are not registered in the system. Please contact an administrator.",
                parse_mode='Markdown'
            )
            return
        
        role = user.get('role', 'unknown')
        role_emoji = {
            'admin': '👑',
            'user': '👤',
            'guest': '👥'
        }.get(role, '❓')
        
        info_text = f"{role_emoji} **Your Account Information**\n\n"
        info_text += f"**Username:** @{user.get('username', 'Unknown')}\n"
        info_text += f"**User ID:** `{user_id}`\n"
        info_text += f"**Role:** {role.title()}\n"
        
        added_at = user.get('added_at')
        if added_at:
            info_text += f"**Joined:** {added_at.strftime('%Y-%m-%d %H:%M')}\n"
        
        last_activity = user.get('last_activity')
        if last_activity:
            info_text += f"**Last Activity:** {last_activity.strftime('%Y-%m-%d %H:%M')}\n"
        
        # Show permissions
        info_text += f"\n**Permissions:**\n"
        permissions = {
            'check_domains': '🔍 Check domains',
            'list_domains': '📋 List domains',
            'add_domains': '➕ Add domains',
            'remove_domains': '➖ Remove domains',
            'manage_users': '👥 Manage users',
            'bulk_operations': '📦 Bulk operations'
        }
        
        for perm, desc in permissions.items():
            has_perm = self.user_service.has_permission(user_id, perm)
            status = "✅" if has_perm else "❌"
            info_text += f"   {status} {desc}\n"
        
        # Show allowed groups for guests
        if role == 'guest':
            allowed_groups = user.get('allowed_groups', [])
            info_text += f"\n**Allowed Groups:** {', '.join(allowed_groups) if allowed_groups else 'None'}\n"
        
        await update.message.reply_text(info_text, parse_mode='Markdown')
    
    async def find_user_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /finduser command to help resolve usernames"""
        user_id = update.effective_user.id
        
        # Check if user is admin
        if not self.user_service.is_admin(user_id):
            await update.message.reply_text(
                "❌ **Access Denied**\n\n"
                "Only administrators can search for users.",
                parse_mode='Markdown'
            )
            return
        
        # Parse command arguments
        args = context.args
        if len(args) < 1:
            await update.message.reply_text(
                "📝 **Find User Usage**\n\n"
                "**Format:** `/finduser @username` or `/finduser username`\n\n"
                "**Examples:**\n"
                "• `/finduser @john_doe`\n"
                "• `/finduser john_doe`\n\n"
                "This searches recent bot interactions for the username.",
                parse_mode='Markdown'
            )
            return
        
        try:
            search_username = args[0].strip().lstrip('@')
            
            # Try to resolve username
            found_user_id = self.user_resolver.resolve_username_to_id(search_username)
            
            if found_user_id:
                # Get additional user info
                user_info = self.user_resolver.get_user_info(found_user_id)
                
                result_text = (
                    f"✅ **User Found**\n\n"
                    f"**Username:** @{search_username}\n"
                    f"**User ID:** `{found_user_id}`\n"
                )
                
                if user_info:
                    if user_info.get('first_name'):
                        result_text += f"**Name:** {user_info['first_name']}\n"
                    if user_info.get('last_seen'):
                        result_text += f"**Last Seen:** {user_info['last_seen'].strftime('%Y-%m-%d %H:%M:%S')}\n"
                
                # Check if user is already registered
                existing_user = self.user_service.get_user(found_user_id)
                if existing_user:
                    result_text += f"\n**Status:** Already registered as {existing_user['role']}\n"
                else:
                    result_text += f"\n**Status:** Not registered\n"
                    result_text += f"\n**To add user:**\n"
                    result_text += f"`/adduser {found_user_id} {search_username} user`"
                
                await update.message.reply_text(result_text, parse_mode='Markdown')
                
            else:
                # Username not found
                result_text = (
                    f"❌ **Username @{search_username} Not Found**\n\n"
                    f"This username hasn't interacted with the bot recently.\n\n"
                    f"{self.user_resolver.suggest_user_id_methods(search_username)}"
                )
                
                await update.message.reply_text(result_text, parse_mode='Markdown')
                
        except Exception as e:
            logger.error(f"Error in find_user_command: {e}")
            await update.message.reply_text(
                "❌ **Error**\n\n"
                "Failed to search for user. Please try again.",
                parse_mode='Markdown'
            )
    
    async def show_user_management_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user management menu (Admin only)"""
        user_id = update.effective_user.id
        
        # Check if user is admin
        if not self.user_service.is_admin(user_id):
            await update.callback_query.answer("❌ Access denied", show_alert=True)
            return
        
        keyboard = [
            [
                InlineKeyboardButton("👥 List Users", callback_data="admin_list_users"),
                InlineKeyboardButton("➕ Add User", callback_data="admin_add_user_help")
            ],
            [
                InlineKeyboardButton("🔧 User Roles", callback_data="admin_user_roles"),
                InlineKeyboardButton("📊 User Stats", callback_data="admin_user_stats")
            ],
            [InlineKeyboardButton("🔙 Back to Main", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "👑 **User Management**\n\n"
            "Select an option to manage users and permissions:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )