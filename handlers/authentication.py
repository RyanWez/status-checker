"""
Authentication handlers for the Telegram bot
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config.settings import settings

logger = logging.getLogger(__name__)

# Conversation states
UNAUTHENTICATED, AUTHENTICATED = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /start command with authentication"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "User"
    
    if settings.is_admin(user_id):
        # Create welcome keyboard
        keyboard = [
            [
                InlineKeyboardButton("📂 View Groups", callback_data="list_groups"),
                InlineKeyboardButton("🔍 Check All", callback_data="check_all")
            ],
            [
                InlineKeyboardButton("📋 All Domains", callback_data="list_domains"),
                InlineKeyboardButton("📊 Group Summary", callback_data="group_summary")
            ],
            [
                InlineKeyboardButton("❓ Help", callback_data="help"),
                InlineKeyboardButton("🚪 Logout", callback_data="logout")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = (
            f"🔐 **Welcome {user_name}!** You are authenticated as admin.\n\n"
            "🤖 **Domain Status Checker Bot**\n"
            "Monitor your domains and get instant notifications when they go down.\n\n"
            "Use the buttons below or these commands:\n"
            "• `/add domain.com [group]` - Add single domain\n"
            "• `/add GroupName domain1.com,domain2.com` - Bulk add domains\n"
            "• `/remove <domain>` - Remove domain from monitoring\n"
            "• `/list` - Show groups and domains\n"
            "• `/checkall` - Check all domains now\n"
            "• `/help` - Show help menu\n\n"
            "**New Features:**\n"
            "• **Bulk Addition:** Add multiple domains with commas\n"
            "• **Group Organization:** Web1, Web2, Production, etc.\n"
            "• **Fast Group Checking:** Check specific groups\n"
            "• **Optimized Performance:** Handles 150+ domains efficiently"
        )
        
        await update.message.reply_text(
            welcome_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        return AUTHENTICATED
    else:
        await update.message.reply_text(
            "❌ **Access Denied**\n\n"
            "This bot is private and only accessible to authorized users.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END

async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle logout command"""
    await update.message.reply_text(
        "👋 **Logged out successfully**\n\n"
        "Use /start to authenticate again.",
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