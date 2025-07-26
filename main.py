#!/usr/bin/env python3
"""
Private Telegram Domain Status Checker Bot
Modern, modular implementation with interactive UI
"""

import logging
import asyncio
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
from telegram.error import BadRequest, TelegramError
# Removed APScheduler import - using Telegram's built-in job queue instead

from config.settings import settings
from services.database import DatabaseService
from services.checker import DomainChecker
from services.user_management import UserManagementService
from handlers.authentication import (
    start, logout, unauthorized_handler, 
    UNAUTHENTICATED, AUTHENTICATED, user_service
)
from handlers.domains import DomainHandlers
from handlers.user_management import UserManagementHandlers
from health_server import health_server

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class DomainBot:
    """Main bot class that orchestrates all components"""
    
    def __init__(self):
        self.db_service = None
        self.user_service = None
        self.domain_handlers = None
        self.user_handlers = None
        self.application = None
    
    async def initialize(self):
        """Initialize all bot components"""
        try:
            logger.info("Initializing bot components...")
            
            # Start health server first
            logger.info("Starting health server...")
            await health_server.start_server()
            health_server.set_bot_status("initializing")
            
            # Initialize database service
            logger.info("Connecting to database...")
            self.db_service = DatabaseService(settings.MONGO_URL)
            
            # Initialize user management service
            logger.info("Setting up user management...")
            self.user_service = UserManagementService(self.db_service)
            
            # Set global user service for authentication
            import handlers.authentication
            handlers.authentication.user_service = self.user_service
            
            # Initialize domain handlers
            logger.info("Setting up domain handlers...")
            self.domain_handlers = DomainHandlers(self.db_service, self.user_service)
            
            # Initialize user management handlers
            logger.info("Setting up user management handlers...")
            self.user_handlers = UserManagementHandlers(self.db_service, self.user_service)
            
            # Create Telegram application
            logger.info("Creating Telegram application...")
            self.application = Application.builder().token(settings.TELEGRAM_TOKEN).build()
            
            # Setup handlers
            logger.info("Setting up command handlers...")
            self._setup_handlers()
            
            # Setup scheduled jobs
            logger.info("Setting up scheduled jobs...")
            self._setup_scheduled_jobs()
            
            health_server.set_bot_status("running")
            logger.info("Bot initialized successfully!")
            
        except Exception as e:
            logger.error(f"Failed to initialize bot: {e}")
            health_server.set_bot_status("error")
            # Clean up any partially initialized components
            if self.db_service:
                try:
                    self.db_service.close()
                except:
                    pass
            raise
    
    def _setup_handlers(self):
        """Setup all Telegram handlers"""
        # Create conversation handler for authentication
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                AUTHENTICATED: [
                    CommandHandler('help', self.domain_handlers.help_command),
                    CommandHandler('add', self.domain_handlers.add_domain),
                    CommandHandler('remove', self.domain_handlers.remove_domain),
                    CommandHandler('list', self.domain_handlers.list_groups),
                    CommandHandler(['checkall', 'check'], self.domain_handlers.check_all_domains),
                    CommandHandler('adduser', self.user_handlers.add_user_command),
                    CommandHandler('removeuser', self.user_handlers.remove_user_command),
                    CommandHandler('listusers', self.user_handlers.list_users_command),
                    CommandHandler('userlists', self.user_handlers.interactive_user_list),
                    CommandHandler('userinfo', self.user_handlers.user_info_command),
                    CommandHandler('finduser', self.user_handlers.find_user_command),
                    CommandHandler('logout', logout),
                    CallbackQueryHandler(self._handle_callback_query),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, unauthorized_handler)
                ]
            },
            fallbacks=[CommandHandler('start', start)],
            per_message=False,
            per_chat=True,
            per_user=True
        )
        
        # Add handlers to application
        self.application.add_handler(conv_handler)
        
        # Add global callback query handler for unauthenticated users
        self.application.add_handler(
            CallbackQueryHandler(self._handle_unauthenticated_callback, pattern=".*")
        )
        
        # Add error handler
        self.application.add_error_handler(self._error_handler)
    
    async def _handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all callback queries for authenticated users"""
        query = update.callback_query
        
        try:
            await query.answer()
        except Exception as e:
            logger.debug(f"Failed to answer callback query: {e}")
        
        data = query.data
        
        # Main menu actions
        if data == "main_menu":
            await start(update, context)
        elif data == "help":
            await self.domain_handlers.help_command(update, context)
        elif data == "list_domains":
            await self.domain_handlers.list_domains(update, context)
        elif data == "list_groups":
            await self.domain_handlers.list_groups(update, context)
        elif data == "check_all":
            await self.domain_handlers.check_all_domains(update, context)
        elif data == "check_all_groups":
            await self.domain_handlers.check_all_groups(update, context)
        elif data == "group_summary":
            await self.domain_handlers.show_group_summary(update, context)
        elif data == "logout":
            await logout(update, context)
        
        # User management actions (Admin only)
        elif data == "user_management":
            await self.user_handlers.show_user_management_menu(update, context)
        elif data == "admin_list_users":
            await self.user_handlers.interactive_user_list(update, context, 0)
        elif data == "admin_add_user_help":
            await self._show_add_user_help(update, context)
        elif data == "admin_user_roles":
            await self._show_user_roles_info(update, context)
        elif data == "admin_user_stats":
            await self._show_user_stats(update, context)
        elif data == "admin_settings":
            await self._show_admin_settings(update, context)
        
        # Interactive user list pagination
        elif data.startswith("users_page_"):
            page = int(data.split("_")[-1])
            await self.user_handlers.interactive_user_list(update, context, page)
        
        # User-specific actions
        elif data.startswith("user_info_"):
            target_user_id = data.replace("user_info_", "")
            await self.user_handlers.show_user_details(update, context, target_user_id)
        elif data.startswith("user_delete_confirm_"):
            target_user_id = data.replace("user_delete_confirm_", "")
            await self.user_handlers.confirm_user_deletion(update, context, target_user_id)
        elif data.startswith("user_delete_"):
            target_user_id = data.replace("user_delete_", "")
            await self.user_handlers.delete_user_confirmed(update, context, target_user_id)
        elif data.startswith("user_change_role_"):
            target_user_id = data.replace("user_change_role_", "")
            await self._show_change_role_menu(update, context, target_user_id)
        elif data.startswith("set_role_"):
            parts = data.split("_")
            target_user_id = parts[2]
            new_role = parts[3]
            await self._change_user_role(update, context, target_user_id, new_role)
        
        # Pagination
        elif data.startswith("list_page_"):
            page = int(data.split("_")[-1])
            await self.domain_handlers.list_domains(update, context, page)
        elif data.startswith("group_page_"):
            parts = data.split("_")
            group_name = parts[2]
            page = int(parts[3])
            await self.domain_handlers.list_domains(update, context, page, group_name)
        
        # Group actions
        elif data.startswith("group_") and not data.startswith("group_page_"):
            group_name = data.replace("group_", "")
            await self.domain_handlers.list_domains(update, context, 0, group_name)
        elif data.startswith("check_group_"):
            group_name = data.replace("check_group_", "")
            await self.domain_handlers.check_group_domains(update, context, group_name)
        
        # Domain-specific actions
        elif data.startswith("check_single_"):
            domain = data.replace("check_single_", "")
            await self._check_single_domain(update, context, domain)
        elif data.startswith("delete_confirm_"):
            domain = data.replace("delete_confirm_", "")
            await self._confirm_delete_domain(update, context, domain)
        elif data.startswith("delete_"):
            domain = data.replace("delete_", "")
            await self._delete_domain(update, context, domain)
        elif data.startswith("domain_info_"):
            domain = data.replace("domain_info_", "")
            await self._show_domain_info(update, context, domain)
        
        # Help sections
        elif data.startswith("help_"):
            await self._show_help_section(update, context, data)
        
        # Show down domain details
        elif data == "show_down_details":
            await self._show_down_details(update, context)
        
        # No-op for pagination info
        elif data == "noop":
            pass
    
    async def _show_add_user_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show help for adding users"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        help_text = (
            "➕ **Add User Help**\n\n"
            "**Command Formats:**\n"
            "• `/adduser <user_id> <username> [role]` - Using User ID\n"
            "• `/adduser @username [role]` - Using Username (if known)\n\n"
            "**Roles:**\n"
            "• `admin` - Full access to all features\n"
            "• `user` - Read-only access to all domains\n"
            "• `guest` - Limited access to assigned groups\n\n"
            "**Examples:**\n"
            "• `/adduser 123456789 john_doe user`\n"
            "• `/adduser @john_doe user` (if user interacted recently)\n"
            "• `/adduser 987654321 jane_admin admin`\n\n"
            "**Finding User ID:**\n"
            "• `/finduser @username` - Search recent interactions\n"
            "• Ask user to send `/start` to bot\n"
            "• Use @userinfobot for User ID lookup\n"
            "• Check bot logs for recent interactions"
        )
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="user_management")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            help_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def _show_user_roles_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show information about user roles"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        roles_text = (
            "🔧 **User Roles & Permissions**\n\n"
            "👑 **Admin**\n"
            "• Add/remove domains\n"
            "• Bulk operations\n"
            "• Manage users\n"
            "• Access all groups\n"
            "• System settings\n\n"
            "👤 **User**\n"
            "• View all domains\n"
            "• Check domain status\n"
            "• Access all groups\n"
            "• Cannot modify domains\n\n"
            "👥 **Guest**\n"
            "• View assigned groups only\n"
            "• Check domain status\n"
            "• Cannot modify anything\n"
            "• Limited access"
        )
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="user_management")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            roles_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def _show_user_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user statistics"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        try:
            users = self.user_service.get_all_users()
            
            # Count by role
            role_counts = {'admin': 0, 'user': 0, 'guest': 0}
            active_users = 0
            
            for user in users:
                role = user.get('role', 'guest')
                role_counts[role] = role_counts.get(role, 0) + 1
                
                if user.get('last_activity'):
                    active_users += 1
            
            stats_text = (
                f"📊 **User Statistics**\n\n"
                f"**Total Users:** {len(users)}\n"
                f"**Active Users:** {active_users}\n\n"
                f"**By Role:**\n"
                f"👑 Admins: {role_counts['admin']}\n"
                f"👤 Users: {role_counts['user']}\n"
                f"👥 Guests: {role_counts['guest']}\n\n"
                f"**System Info:**\n"
                f"• Total Domains: {self.db_service.get_domains_count()}\n"
                f"• Total Groups: {len(self.db_service.get_groups())}"
            )
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            stats_text = "❌ **Error**\n\nFailed to load user statistics."
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="user_management")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            stats_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def _show_admin_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show admin settings"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        settings_text = (
            "⚙️ **Admin Settings**\n\n"
            "**Current Configuration:**\n"
            f"• Check Interval: 5 minutes\n"
            f"• Connection Timeout: 10 seconds\n"
            f"• Max Concurrent Checks: 100\n"
            f"• Domains per Page: 5\n\n"
            "**System Status:**\n"
            f"• Bot Status: Running\n"
            f"• Database: Connected\n"
            f"• Health Server: Active\n\n"
            "**Features:**\n"
            "• Role-based Access Control: ✅\n"
            "• User Management: ✅\n"
            "• Group Organization: ✅\n"
            "• Bulk Operations: ✅"
        )
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="user_management")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            settings_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def _show_change_role_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, target_user_id: str):
        """Show role change menu for a user"""
        user_id = update.effective_user.id
        
        # Check if user is admin
        if not self.user_service.is_admin(user_id):
            await update.callback_query.answer("❌ Access Denied", show_alert=True)
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
            current_role = target_user.get('role', 'unknown').title()
            
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            
            keyboard = [
                [
                    InlineKeyboardButton("👑 Admin", callback_data=f"set_role_{target_user_id}_admin"),
                    InlineKeyboardButton("👤 User", callback_data=f"set_role_{target_user_id}_user")
                ],
                [
                    InlineKeyboardButton("👥 Guest", callback_data=f"set_role_{target_user_id}_guest")
                ],
                [
                    InlineKeyboardButton("🔙 Back", callback_data=f"user_info_{target_user_id}"),
                    InlineKeyboardButton("❌ Cancel", callback_data="users_page_0")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                f"🔄 **Change User Role**\n\n"
                f"**Username:** @{username}\n"
                f"**User ID:** `{target_user_id}`\n"
                f"**Current Role:** {current_role}\n\n"
                f"**Select new role:**\n"
                f"👑 **Admin** - Full access to all features\n"
                f"👤 **User** - Read-only access to all domains\n"
                f"👥 **Guest** - Limited access to assigned groups",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error in _show_change_role_menu: {e}")
            await update.callback_query.edit_message_text(
                "❌ **Error**\n\nFailed to load role change menu.",
                parse_mode='Markdown'
            )
    
    async def _change_user_role(self, update: Update, context: ContextTypes.DEFAULT_TYPE, target_user_id: str, new_role: str):
        """Change a user's role"""
        user_id = update.effective_user.id
        
        # Check if user is admin
        if not self.user_service.is_admin(user_id):
            await update.callback_query.answer("❌ Access Denied", show_alert=True)
            return
        
        try:
            from services.user_management import UserRole
            
            # Validate role
            role_map = {
                'admin': UserRole.ADMIN,
                'user': UserRole.USER,
                'guest': UserRole.GUEST
            }
            
            if new_role not in role_map:
                await update.callback_query.edit_message_text(
                    "❌ **Invalid Role**\n\nPlease select a valid role.",
                    parse_mode='Markdown'
                )
                return
            
            target_user = self.user_service.get_user(int(target_user_id))
            
            if not target_user:
                await update.callback_query.edit_message_text(
                    f"❌ **User Not Found**\n\nUser ID `{target_user_id}` not found.",
                    parse_mode='Markdown'
                )
                return
            
            username = target_user.get('username', 'Unknown')
            old_role = target_user.get('role', 'unknown').title()
            new_role_obj = role_map[new_role]
            
            # Don't allow changing own role to non-admin
            if int(target_user_id) == user_id and new_role_obj != UserRole.ADMIN:
                await update.callback_query.answer(
                    "❌ Cannot change your own role to non-admin", 
                    show_alert=True
                )
                return
            
            # Update role
            if self.user_service.update_user_role(int(target_user_id), new_role_obj, user_id):
                role_emoji = {
                    'admin': '👑',
                    'user': '👤',
                    'guest': '👥'
                }
                
                await update.callback_query.edit_message_text(
                    f"✅ **Role Changed Successfully**\n\n"
                    f"**Username:** @{username}\n"
                    f"**User ID:** `{target_user_id}`\n"
                    f"**Old Role:** {old_role}\n"
                    f"**New Role:** {role_emoji.get(new_role, '❓')} {new_role.title()}\n\n"
                    f"The user's permissions have been updated.",
                    parse_mode='Markdown'
                )
                
                # Auto-redirect to user details after 2 seconds
                await asyncio.sleep(2)
                await self.user_handlers.show_user_details(update, context, target_user_id)
            else:
                await update.callback_query.edit_message_text(
                    f"❌ **Failed to Change Role**\n\n"
                    f"Could not update role for user `{target_user_id}`. Please try again.",
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            logger.error(f"Error in _change_user_role: {e}")
            await update.callback_query.edit_message_text(
                "❌ **Error**\n\nFailed to change user role. Please try again.",
                parse_mode='Markdown'
            )
    
    async def _handle_unauthenticated_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from unauthenticated users"""
        query = update.callback_query
        try:
            await query.answer("❌ Please authenticate first using /start", show_alert=True)
        except Exception as e:
            logger.debug(f"Failed to answer unauthenticated callback: {e}")
    
    async def _error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors in the bot"""
        logger.error(f"Exception while handling an update: {context.error}")
        
        # Handle specific Telegram API errors
        if isinstance(context.error, BadRequest):
            if "Message is not modified" in str(context.error):
                # This is a common error when trying to edit a message with the same content
                if update.callback_query:
                    try:
                        await update.callback_query.answer("✅ Already up to date!")
                    except Exception:
                        pass
                return
            
            # Handle other BadRequest errors
            if update.callback_query:
                try:
                    await update.callback_query.answer("❌ Something went wrong. Please try again.")
                except Exception:
                    pass
            elif update.message:
                try:
                    await update.message.reply_text("❌ Something went wrong. Please try again.")
                except Exception:
                    pass
            return
        
        # Handle other Telegram errors
        if isinstance(context.error, TelegramError):
            logger.error(f"Telegram error: {context.error}")
            return
        
        # For other errors, log them but don't crash the bot
        logger.error(f"Unhandled error: {context.error}")
    
    async def _check_single_domain(self, update: Update, context: ContextTypes.DEFAULT_TYPE, domain: str):
        """Check a single domain and update the message"""
        # Show checking status
        await update.callback_query.edit_message_text(
            f"🔄 **Checking domain:** `{domain}`\n\nPlease wait...",
            parse_mode='Markdown'
        )
        
        # Perform check
        result = DomainChecker.check_domain_sync(domain)
        self.db_service.update_domain_status(domain, result)
        
        # Format result
        status_emoji = "✅" if result['status'] == 'up' else "🚨"
        response_time_text = f" ({result['response_time']:.2f}s)" if result['response_time'] else ""
        error_text = f"\n**Error:** `{result['error']}`" if result['error'] else ""
        
        # Create buttons
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [
            [
                InlineKeyboardButton("🔄 Check Again", callback_data=f"check_single_{domain}"),
                InlineKeyboardButton("📋 Back to List", callback_data="list_domains")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            f"🔍 **Domain Check Result**\n\n"
            f"**Domain:** `{domain}`\n"
            f"**Status:** {status_emoji} {result['status'].upper()}{response_time_text}"
            f"{error_text}\n"
            f"**Checked:** {format_myanmar_time(result['timestamp'])}",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def _confirm_delete_domain(self, update: Update, context: ContextTypes.DEFAULT_TYPE, domain: str):
        """Show confirmation dialog for domain deletion"""
        # Check permission
        user_id = update.effective_user.id
        if not self.user_service or not self.user_service.has_permission(user_id, 'remove_domains'):
            await update.callback_query.answer(
                "❌ Access Denied\n\nYou don't have permission to remove domains.", 
                show_alert=True
            )
            return
        
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Yes, Delete", callback_data=f"delete_{domain}"),
                InlineKeyboardButton("❌ Cancel", callback_data="list_domains")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            f"🗑️ **Confirm Deletion**\n\n"
            f"Are you sure you want to remove `{domain}` from monitoring?\n\n"
            f"This action cannot be undone.",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def _delete_domain(self, update: Update, context: ContextTypes.DEFAULT_TYPE, domain: str):
        """Delete a domain from monitoring"""
        # Check permission
        user_id = update.effective_user.id
        if not self.user_service or not self.user_service.has_permission(user_id, 'remove_domains'):
            await update.callback_query.answer(
                "❌ Access Denied\n\nYou don't have permission to remove domains.", 
                show_alert=True
            )
            return
        
        if self.db_service.remove_domain(domain):
            await update.callback_query.edit_message_text(
                f"✅ **Domain Removed**\n\n"
                f"Domain `{domain}` has been removed from monitoring.",
                parse_mode='Markdown'
            )
            # Show updated list after a moment
            await asyncio.sleep(1)
            await self.domain_handlers.list_domains(update, context)
        else:
            await update.callback_query.edit_message_text(
                f"❌ **Deletion Failed**\n\n"
                f"Could not remove domain `{domain}`. It may not exist.",
                parse_mode='Markdown'
            )
    
    async def _show_domain_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE, domain: str):
        """Show detailed information about a domain"""
        domain_doc = self.db_service.get_domain(domain)
        
        if not domain_doc:
            await update.callback_query.edit_message_text(
                f"❌ **Domain Not Found**\n\n"
                f"Domain `{domain}` is not in the monitoring list.",
                parse_mode='Markdown'
            )
            return
        
        # Format domain information
        status = domain_doc.get('last_status', 'unknown')
        status_emoji = {'up': '✅', 'down': '🚨', 'unknown': '⚪'}.get(status, '⚪')
        
        added_at = domain_doc.get('added_at')
        last_checked = domain_doc.get('last_checked')
        response_time = domain_doc.get('last_response_time')
        status_code = domain_doc.get('last_status_code')
        error = domain_doc.get('last_error')
        
        info_text = (
            f"ℹ️ **Domain Information**\n\n"
            f"**Domain:** `{domain}`\n"
            f"**Status:** {status_emoji} {status.upper()}\n"
        )
        
        if added_at:
            from utils.timezone import format_myanmar_time
            info_text += f"**Added:** {format_myanmar_time(added_at)}\n"
        
        if last_checked:
            info_text += f"**Last Checked:** {format_myanmar_time(last_checked)}\n"
        
        if response_time:
            info_text += f"**Response Time:** {response_time:.2f}s\n"
        
        if status_code:
            info_text += f"**Status Code:** {status_code}\n"
        
        if error:
            info_text += f"**Error:** `{error}`\n"
        
        # Create action buttons
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        # Check if user can delete domains
        user_id = update.effective_user.id
        can_delete = self.user_service and self.user_service.has_permission(user_id, 'remove_domains')
        
        # Create first row with check button and conditionally delete button
        first_row = [InlineKeyboardButton("🔄 Check Now", callback_data=f"check_single_{domain}")]
        if can_delete:
            first_row.append(InlineKeyboardButton("🗑️ Delete", callback_data=f"delete_confirm_{domain}"))
        
        keyboard = [
            first_row,
            [InlineKeyboardButton("📋 Back to List", callback_data="list_domains")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            info_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def _show_help_section(self, update: Update, context: ContextTypes.DEFAULT_TYPE, section: str):
        """Show specific help section"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        help_texts = {
            "help_add": (
                "➕ **Adding Domains**\n\n"
                "**Single Domain:**\n"
                "• `/add domain.com [group]` - Add single domain\n\n"
                "**Bulk Addition (NEW!):**\n"
                "• `/add GroupName domain1.com,domain2.com,domain3.com`\n"
                "• Much faster for adding multiple domains\n\n"
                "**Examples:**\n"
                "• `/add google.com Web1` (single domain)\n"
                "• `/add Web1 google.com,facebook.com,github.com` (bulk)\n"
                "• `/add Production site1.com,site2.com,site3.com` (bulk)\n\n"
                "**Bulk Benefits:**\n"
                "• Add many domains at once with comma separation\n"
                "• Concurrent checking for faster processing\n"
                "• Perfect for large domain lists (150+)\n"
                "• Automatic validation and error reporting\n\n"
                "**Group Benefits:**\n"
                "• Organize domains logically (Web1, Web2, Production, etc.)\n"
                "• Check specific groups independently\n"
                "• Better performance with many domains"
            ),
            "help_remove": (
                "➖ **Removing Domains**\n\n"
                "Use `/remove <domain>` to remove a domain from monitoring.\n\n"
                "**Example:**\n"
                "• `/remove google.com`\n\n"
                "You can also use the 🗑️ button in the domain list for interactive removal."
            ),
            "help_list": (
                "📋 **Listing Domains**\n\n"
                "Use `/list` to see domains organized by groups.\n\n"
                "**New Group Interface:**\n"
                "• Shows all groups with domain counts and status\n"
                "• Click on a group to view its domains\n"
                "• Quick action buttons (🔄 Check, 🗑️ Delete)\n"
                "• Status indicators (✅ UP, 🚨 DOWN, ⚪ Unknown)\n"
                "• Domains sorted by status (DOWN first)\n"
                "• Pagination for large groups\n\n"
                "**Group Benefits:**\n"
                "• Better organization for 150+ domains\n"
                "• Faster navigation and checking\n"
                "• Group-specific monitoring"
            ),
            "help_check": (
                "🔍 **Checking Domains**\n\n"
                "Multiple ways to check domains:\n\n"
                "**Check All:** `/checkall` or `/check`\n"
                "• Checks all domains across all groups\n"
                "• Optimized for 150+ domains\n"
                "• Uses bulk database updates\n\n"
                "**Check by Group:** Use group interface\n"
                "• Check specific groups independently\n"
                "• Faster for targeted monitoring\n"
                "• Better resource management\n\n"
                "**Performance Features:**\n"
                "• Concurrent checking (up to 100 simultaneous)\n"
                "• Batch processing for large domain lists\n"
                "• Optimized timeouts and connection pooling\n"
                "• Real-time progress updates\n"
                "• Detailed results with response times"
            ),
            "help_notifications": (
                "🔔 **Notifications**\n\n"
                "The bot automatically checks all domains every 5 minutes.\n\n"
                "**You'll be notified when:**\n"
                "• A domain goes DOWN (UP → DOWN)\n"
                "• Includes error details and timestamp\n\n"
                "**Note:** You won't be spammed with repeated DOWN notifications."
            ),
            "help_settings": (
                "⚙️ **Settings & Features**\n\n"
                "**Authentication:** Private bot for authorized users only\n"
                "**Database:** MongoDB for persistent storage\n"
                "**Monitoring:** 5-minute automatic checks\n"
                "**Timeout:** 10-second connection timeout\n"
                "**Concurrency:** Multiple domains checked simultaneously"
            )
        }
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Help", callback_data="help")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = help_texts.get(section, "❌ Help section not found.")
        
        await update.callback_query.edit_message_text(
            text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def _show_down_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show detailed information about down domains"""
        domains = self.db_service.get_all_domains()
        down_domains = [d for d in domains if d.get('last_status') == 'down']
        
        if not down_domains:
            await update.callback_query.edit_message_text(
                "✅ **All Domains Are UP**\n\n"
                "No domains are currently down. Great job!",
                parse_mode='Markdown'
            )
            return
        
        details_text = f"🚨 **DOWN Domains Details** ({len(down_domains)} total)\n\n"
        
        for domain_doc in down_domains[:10]:  # Limit to 10
            domain = domain_doc['domain']
            error = domain_doc.get('last_error', 'Unknown error')
            last_checked = domain_doc.get('last_checked')
            
            details_text += f"**{domain}**\n"
            details_text += f"• Error: `{error}`\n"
            if last_checked:
                from utils.timezone import format_myanmar_time
                details_text += f"• Last checked: {format_myanmar_time(last_checked)}\n"
            details_text += "\n"
        
        if len(down_domains) > 10:
            details_text += f"*... and {len(down_domains) - 10} more domains*\n"
        
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [
            [
                InlineKeyboardButton("🔄 Check All Again", callback_data="check_all"),
                InlineKeyboardButton("📋 Back to List", callback_data="list_domains")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            details_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    def _setup_scheduled_jobs(self):
        """Setup scheduled background jobs using Telegram's job queue"""
        # Add domain checking job (every 5 minutes)
        job_queue = self.application.job_queue
        job_queue.run_repeating(
            self._scheduled_domain_check,
            interval=timedelta(minutes=5),
            first=timedelta(seconds=30),  # Start after 30 seconds
            name='domain_check'
        )
        
        logger.info("Scheduled jobs configured")
    
    async def _scheduled_domain_check(self, context: ContextTypes.DEFAULT_TYPE):
        """Scheduled background check for all domains"""
        try:
            domains = self.db_service.get_all_domains()
            
            if not domains:
                return
            
            logger.info(f"Running scheduled check for {len(domains)} domains")
            
            # Check all domains with optimized performance
            domain_names = [d['domain'] for d in domains]
            results = await DomainChecker.check_multiple_domains(domain_names, max_concurrent=100)
            
            # Process results and send notifications
            notifications_sent = 0
            status_updates = []
            
            for result in results:
                domain = result['domain']
                current_status = result['status']
                
                # Get previous status
                domain_doc = self.db_service.get_domain(domain)
                previous_status = domain_doc.get('last_status') if domain_doc else None
                
                # Prepare bulk update
                status_updates.append({'domain': domain, 'status_data': result})
                
                # Send notification if status changed to DOWN
                if previous_status == 'up' and current_status == 'down':
                    await self._send_down_notification(domain, result, context)
                    notifications_sent += 1
            
            # Bulk update database for better performance
            if status_updates:
                self.db_service.bulk_update_status(status_updates)
            
            if notifications_sent > 0:
                logger.info(f"Sent {notifications_sent} down notifications")
            
        except Exception as e:
            logger.error(f"Error in scheduled domain check: {e}")
    
    async def _send_down_notification(self, domain: str, result: Dict, context: ContextTypes.DEFAULT_TYPE):
        """Send notification to all bot users about domain going down"""
        error_msg = result.get('error', 'Unknown error')
        # Convert to Myanmar timezone for display
        from utils.timezone import format_myanmar_time
        timestamp = format_myanmar_time(result['timestamp'])
        
        notification = (
            f"🚨 **DOMAIN DOWN ALERT**\n\n"
            f"**Domain:** `{domain}`\n"
            f"**Status:** DOWN\n"
            f"**Error:** `{error_msg}`\n"
            f"**Time:** {timestamp}"
        )
        
        # Get all bot users (admins + registered users)
        all_users = []
        
        # Add legacy admins from settings
        all_users.extend(settings.ADMIN_CHAT_IDS)
        
        # Add registered users from database
        if self.user_service:
            registered_users = self.user_service.get_all_users()
            for user in registered_users:
                user_id = user.get('user_id')
                if user_id and user_id not in all_users:
                    all_users.append(user_id)
        
        # Send notification to all users
        notifications_sent = 0
        for user_id in all_users:
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=notification,
                    parse_mode='Markdown'
                )
                logger.info(f"Sent down alert for {domain} to user {user_id}")
                notifications_sent += 1
            except Exception as e:
                logger.error(f"Failed to send notification to user {user_id}: {e}")
        
        logger.info(f"Sent domain down notification to {notifications_sent}/{len(all_users)} users")
    
    async def start(self):
        """Start the bot"""
        try:
            # Start bot
            logger.info("Starting bot...")
            logger.info(f"Admin chat IDs: {settings.ADMIN_CHAT_IDS}")
            
            # Initialize and start the application
            await self.application.initialize()
            await self.application.start()
            
            # Start polling
            await self.application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
            
            # Keep running until interrupted
            try:
                # This will run indefinitely until interrupted
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                pass
            
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Bot error: {e}")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Gracefully shutdown the bot"""
        logger.info("Shutting down bot...")
        health_server.set_bot_status("shutting_down")
        
        try:
            # Stop the updater
            if self.application and self.application.updater:
                await self.application.updater.stop()
            
            # Stop the application
            if self.application:
                await self.application.stop()
                await self.application.shutdown()
        except Exception as e:
            logger.error(f"Error during application shutdown: {e}")
        
        # Close database connection
        if self.db_service:
            self.db_service.close()
        
        # Stop health server
        await health_server.stop_server()
        
        logger.info("Bot shutdown complete")

async def main():
    """Main entry point"""
    bot = None
    
    try:
        # Create and initialize bot
        bot = DomainBot()
        await bot.initialize()
        
        # Start bot
        await bot.start()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise
    finally:
        if bot:
            await bot.shutdown()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)