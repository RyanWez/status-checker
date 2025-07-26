"""
Authentication handlers for the Telegram bot
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config.settings import settings
from services.user_management import UserManagementService, UserRole

logger = logging.getLogger(__name__)

# Conversation states
UNAUTHENTICATED, AUTHENTICATED = range(2)

# Global user service (will be set by main bot)
user_service: UserManagementService = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /start command with authentication"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "User"
    username = update.effective_user.username or "unknown"
    
    # Update user activity if they exist
    if user_service:
        user_service.update_user_activity(user_id)
        
        # Record user interaction for username resolution
        from services.user_resolver import UserResolver
        user_resolver = UserResolver(user_service.db_service)
        user_resolver.record_user_interaction(user_id, username, user_name)
    
    # Check if user is admin (legacy support)
    is_legacy_admin = settings.is_admin(user_id)
    
    # Check user role from database
    user_role = UserRole.GUEST
    if user_service:
        user_role = user_service.get_user_role(user_id)
    
    # If legacy admin but not in database, add them
    if is_legacy_admin and user_service and not user_service.get_user(user_id):
        user_service.add_user(user_id, username, UserRole.ADMIN)
        user_role = UserRole.ADMIN
    
    # Check if user has access
    has_access = is_legacy_admin or (user_service and user_service.get_user(user_id))
    
    if has_access:
        # Create role-specific welcome keyboard
        keyboard = []
        
        # Basic buttons for all users
        keyboard.append([
            InlineKeyboardButton("📂 View Groups", callback_data="list_groups"),
            InlineKeyboardButton("🔍 Check All", callback_data="check_all")
        ])
        
        keyboard.append([
            InlineKeyboardButton("📋 All Domains", callback_data="list_domains"),
            InlineKeyboardButton("📊 Group Summary", callback_data="group_summary")
        ])
        
        # Admin-only buttons
        if user_role == UserRole.ADMIN:
            keyboard.append([
                InlineKeyboardButton("👥 Manage Users", callback_data="user_management"),
                InlineKeyboardButton("⚙️ Settings", callback_data="admin_settings")
            ])
        
        keyboard.append([
            InlineKeyboardButton("❓ Help", callback_data="help"),
            InlineKeyboardButton("🚪 Logout", callback_data="logout")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Role-specific welcome message
        role_emoji = {
            UserRole.ADMIN: "👑",
            UserRole.USER: "👤", 
            UserRole.GUEST: "👥"
        }
        
        role_permissions = {
            UserRole.ADMIN: "Full access to all features",
            UserRole.USER: "Read-only access to all domains",
            UserRole.GUEST: "Limited access to assigned groups"
        }
        
        welcome_text = (
            f"🔐 **Welcome {user_name}!** {role_emoji.get(user_role, '❓')}\n"
            f"**Role:** {user_role.value.title()}\n"
            f"**Access:** {role_permissions.get(user_role, 'Limited access')}\n\n"
            "🤖 **Domain Status Checker Bot**\n"
            "Monitor your domains and get instant notifications when they go down.\n\n"
        )
        
        # Add role-specific commands
        if user_role == UserRole.ADMIN:
            welcome_text += (
                "**Admin Commands:**\n"
                "• `/add domain.com [group]` - Add single domain\n"
                "• `/add GroupName domain1.com,domain2.com` - Bulk add domains\n"
                "• `/remove <domain>` - Remove domain from monitoring\n"
                "• `/adduser <user_id> <username> [role]` - Add user\n"
                "• `/adduser @username [role]` - Add user by username (if known)\n"
                "• `/finduser @username` - Find user ID by username\n"
                "• `/removeuser <user_id>` - Remove user\n"
                "• `/listusers` - List all users (text format)\n"
                "• `/userlists` - Interactive user management\n\n"
            )
        
        welcome_text += (
            "**Available Commands:**\n"
            "• `/list` - Show groups and domains\n"
            "• `/checkall` - Check all domains now\n"
            "• `/userinfo` - Show your account info\n"
            "• `/help` - Show help menu\n\n"
            "**Features:**\n"
            "• **Group Organization:** Web1, Web2, Production, etc.\n"
            "• **Fast Group Checking:** Check specific groups\n"
            "• **Optimized Performance:** Handles 150+ domains efficiently\n"
            "• **Role-based Access:** Different permissions for different users"
        )
        
        # Handle callback query or message
        if update.callback_query:
            await update.callback_query.edit_message_text(
                welcome_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                welcome_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        
        return AUTHENTICATED
    else:
        await update.message.reply_text(
            "❌ **Access Denied**\n\n"
            "This bot is private and only accessible to authorized users.\n"
            "Please contact an administrator to request access.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END

async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle logout command"""
    logout_text = (
        "👋 **Logged out successfully**\n\n"
        "Use /start to authenticate again."
    )
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            logout_text,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            logout_text,
            parse_mode='Markdown'
        )
    
    return ConversationHandler.END

async def unauthorized_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle unauthorized access attempts"""
    await update.message.reply_text(
        "❌ **Unauthorized**\n\n"
        "Please use /start to authenticate first.",
        parse_mode='Markdown'
    )
    return UNAUTHENTICATED