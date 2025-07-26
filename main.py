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
from handlers.authentication import (
    start, logout, unauthorized_handler, 
    UNAUTHENTICATED, AUTHENTICATED
)
from handlers.domains import DomainHandlers

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
        self.domain_handlers = None
        self.application = None
    
    async def initialize(self):
        """Initialize all bot components"""
        try:
            logger.info("Initializing bot components...")
            
            # Initialize database service
            logger.info("Connecting to database...")
            self.db_service = DatabaseService(settings.MONGO_URL)
            
            # Initialize domain handlers
            logger.info("Setting up domain handlers...")
            self.domain_handlers = DomainHandlers(self.db_service)
            
            # Create Telegram application
            logger.info("Creating Telegram application...")
            self.application = Application.builder().token(settings.TELEGRAM_TOKEN).build()
            
            # Setup handlers
            logger.info("Setting up command handlers...")
            self._setup_handlers()
            
            # Setup scheduled jobs
            logger.info("Setting up scheduled jobs...")
            self._setup_scheduled_jobs()
            
            logger.info("Bot initialized successfully!")
            
        except Exception as e:
            logger.error(f"Failed to initialize bot: {e}")
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
            f"**Checked:** {result['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def _confirm_delete_domain(self, update: Update, context: ContextTypes.DEFAULT_TYPE, domain: str):
        """Show confirmation dialog for domain deletion"""
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
            info_text += f"**Added:** {added_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        if last_checked:
            info_text += f"**Last Checked:** {last_checked.strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        if response_time:
            info_text += f"**Response Time:** {response_time:.2f}s\n"
        
        if status_code:
            info_text += f"**Status Code:** {status_code}\n"
        
        if error:
            info_text += f"**Error:** `{error}`\n"
        
        # Create action buttons
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [
            [
                InlineKeyboardButton("🔄 Check Now", callback_data=f"check_single_{domain}"),
                InlineKeyboardButton("🗑️ Delete", callback_data=f"delete_confirm_{domain}")
            ],
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
                details_text += f"• Last checked: {last_checked.strftime('%Y-%m-%d %H:%M:%S')}\n"
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
        """Send notification to all admins about domain going down"""
        error_msg = result.get('error', 'Unknown error')
        timestamp = result['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        
        notification = (
            f"🚨 **DOMAIN DOWN ALERT**\n\n"
            f"**Domain:** `{domain}`\n"
            f"**Status:** DOWN\n"
            f"**Error:** `{error_msg}`\n"
            f"**Time:** {timestamp}"
        )
        
        # Send to all admin chat IDs
        for admin_id in settings.ADMIN_CHAT_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=notification,
                    parse_mode='Markdown'
                )
                logger.info(f"Sent down alert for {domain} to admin {admin_id}")
            except Exception as e:
                logger.error(f"Failed to send notification to admin {admin_id}: {e}")
    
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