"""
Domain management handlers for the Telegram bot
"""
import logging
import math
from datetime import datetime
from typing import List, Dict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import ContextTypes
from services.database import DatabaseService
from services.checker import DomainChecker
from services.user_management import UserManagementService
from handlers.authentication import AUTHENTICATED

logger = logging.getLogger(__name__)

def require_permission(permission: str):
    """Decorator to check user permissions"""
    def decorator(func):
        async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_id = update.effective_user.id
            
            if not self.user_service or not self.user_service.has_permission(user_id, permission):
                error_msg = f"❌ **Access Denied**\n\nYou don't have permission to {permission.replace('_', ' ')}."
                
                if update.callback_query:
                    await update.callback_query.answer(error_msg, show_alert=True)
                else:
                    await update.message.reply_text(error_msg, parse_mode='Markdown')
                return AUTHENTICATED
            
            return await func(self, update, context, *args, **kwargs)
        return wrapper
    return decorator

class DomainHandlers:
    """Handlers for domain-related commands"""
    
    def __init__(self, db_service: DatabaseService, user_service: UserManagementService = None):
        self.db = db_service
        self.user_service = user_service
        self.DOMAINS_PER_PAGE = 5
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show interactive help menu"""
        keyboard = [
            [
                InlineKeyboardButton("➕ Adding Domains", callback_data="help_add"),
                InlineKeyboardButton("➖ Removing Domains", callback_data="help_remove")
            ],
            [
                InlineKeyboardButton("📋 Listing Domains", callback_data="help_list"),
                InlineKeyboardButton("🔍 Checking Domains", callback_data="help_check")
            ],
            [
                InlineKeyboardButton("🔔 Notifications", callback_data="help_notifications"),
                InlineKeyboardButton("⚙️ Settings", callback_data="help_settings")
            ],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        help_text = (
            "🤖 **Domain Status Checker Bot Help**\n\n"
            "Select a category below to learn more about the bot's features:"
        )
        
        if update.callback_query:
            try:
                await update.callback_query.edit_message_text(
                    help_text,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            except Exception as e:
                await update.callback_query.answer("Help menu loaded!")
                logger.debug(f"Failed to edit help message: {e}")
        else:
            await update.message.reply_text(
                help_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        return AUTHENTICATED
    
    @require_permission('add_domains')
    async def add_domain(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Add domain(s) to monitoring with optional group - supports bulk addition"""
        if not context.args:
            await update.message.reply_text(
                "❌ **Missing Domain**\n\n"
                "**Single domain:** `/add example.com [group_name]`\n"
                "**Bulk domains:** `/add GroupName domain1.com,domain2.com,domain3.com`\n\n"
                "**Examples:**\n"
                "• `/add google.com Web1`\n"
                "• `/add Web1 google.com,facebook.com,github.com`\n\n"
                "**Limits:**\n"
                "• Maximum 50 domains per bulk addition\n"
                "• Duplicates are automatically skipped\n"
                "• Invalid domains are reported but don't stop the process",
                parse_mode='Markdown'
            )
            return AUTHENTICATED
        
        # Check if this is bulk addition (contains comma)
        first_arg = context.args[0].strip()
        
        # Join all arguments to handle spaces in group names and long domain lists
        full_command = ' '.join(context.args).strip()
        
        if ',' in full_command:
            # This is bulk addition
            if ',' in first_arg:
                # Format: /add domain1,domain2,domain3 (no group specified)
                group_name = "Default"
                domains_input = first_arg
            else:
                # Format: /add GroupName domain1,domain2,domain3
                # Find where the comma-separated domains start
                parts = full_command.split(' ', 1)
                if len(parts) == 2 and ',' in parts[1]:
                    group_name = parts[0]
                    domains_input = parts[1]
                else:
                    group_name = "Default"
                    domains_input = full_command
        else:
            # Single domain addition: /add domain [group]
            return await self._add_single_domain(update, context)
        
        # Parse comma-separated domains
        domains = [d.strip().lower() for d in domains_input.split(',') if d.strip()]
        
        if not domains:
            await update.message.reply_text(
                "❌ **No Valid Domains Found**\n\n"
                "Please provide comma-separated domains.\n"
                "**Example:** `/add Web1 google.com,facebook.com,github.com`",
                parse_mode='Markdown'
            )
            return AUTHENTICATED
        
        # Check domain limit (max 50 domains per bulk addition)
        MAX_BULK_DOMAINS = 50
        if len(domains) > MAX_BULK_DOMAINS:
            await update.message.reply_text(
                f"❌ **Too Many Domains**\n\n"
                f"Maximum {MAX_BULK_DOMAINS} domains per bulk addition.\n"
                f"You provided {len(domains)} domains.\n\n"
                f"Please split into smaller batches:\n"
                f"• Batch 1: First {MAX_BULK_DOMAINS} domains\n"
                f"• Batch 2: Remaining domains",
                parse_mode='Markdown'
            )
            return AUTHENTICATED
        
        # Validate domains
        valid_domains = []
        invalid_domains = []
        
        for domain in domains:
            if domain and '.' in domain and len(domain) >= 3:
                valid_domains.append(domain)
            else:
                invalid_domains.append(domain)
        
        if not valid_domains:
            await update.message.reply_text(
                f"❌ **No Valid Domains**\n\n"
                f"Invalid domains: {', '.join(invalid_domains)}\n"
                "Please provide valid domain names.",
                parse_mode='Markdown'
            )
            return AUTHENTICATED
        
        # Send initial message
        status_msg = await update.message.reply_text(
            f"🔄 **Adding {len(valid_domains)} domains to group:** `{group_name}`\n\n"
            "Please wait while I add and check all domains...",
            parse_mode='Markdown'
        )
        
        # Add domains in bulk using efficient bulk method
        bulk_result = self.db.bulk_add_domains(valid_domains, group_name)
        added_domains = bulk_result['added']
        existing_domains = bulk_result['existing']
        existing_same_group = bulk_result.get('existing_same_group', [])
        existing_other_groups = bulk_result.get('existing_other_groups', [])
        
        if not added_domains:
            # Create detailed message about why no domains were added
            message_parts = ["❌ **No New Domains Added**\n\n"]
            
            if existing_same_group:
                message_parts.append(f"**Already in group `{group_name}`:**\n")
                message_parts.append(f"{', '.join(existing_same_group)}\n\n")
            
            if existing_other_groups:
                message_parts.append("**Already monitored in other groups:**\n")
                for domain_info in existing_other_groups:
                    message_parts.append(f"• {domain_info}\n")
                message_parts.append("\n")
            
            if invalid_domains:
                message_parts.append(f"**Invalid domains:** {', '.join(invalid_domains)}")
            
            await status_msg.edit_text(
                ''.join(message_parts),
                parse_mode='Markdown'
            )
            return AUTHENTICATED
        
        # Check all added domains concurrently
        results = await DomainChecker.check_multiple_domains(added_domains, max_concurrent=20)
        
        # Update database with results
        status_updates = [{'domain': r['domain'], 'status_data': r} for r in results]
        self.db.bulk_update_status(status_updates)
        
        # Generate summary
        up_count = sum(1 for r in results if r['status'] == 'up')
        down_count = len(results) - up_count
        
        # Create result message
        result_text = f"✅ **Bulk Addition Complete**\n\n"
        result_text += f"**Group:** `{group_name}`\n"
        result_text += f"**Added:** {len(added_domains)} new domains\n"
        result_text += f"**Status:** ✅ {up_count} UP | 🚨 {down_count} DOWN\n\n"
        
        # Show detailed information about skipped domains
        if existing_same_group:
            result_text += f"**Already in this group:** {len(existing_same_group)} domains\n"
        
        if existing_other_groups:
            result_text += f"**In other groups:** {len(existing_other_groups)} domains\n"
        
        if invalid_domains:
            result_text += f"**Invalid:** {len(invalid_domains)} domains\n"
        
        # Show summary of what was processed
        total_processed = len(added_domains) + len(existing_domains) + len(invalid_domains)
        result_text += f"\n**Total processed:** {total_processed} domains"
        
        # Show some added domains
        if added_domains:
            result_text += f"\n**✅ Added domains:**\n"
            for result in results[:10]:  # Show first 10
                status_emoji = "✅" if result['status'] == 'up' else "🚨"
                result_text += f"• {status_emoji} `{result['domain']}`\n"
            
            if len(results) > 10:
                result_text += f"*... and {len(results) - 10} more*\n"
        
        # Show existing domains in other groups (if any)
        if existing_other_groups:
            result_text += f"\n**ℹ️ Already monitored elsewhere:**\n"
            for domain_info in existing_other_groups[:5]:  # Show first 5
                result_text += f"• `{domain_info}`\n"
            
            if len(existing_other_groups) > 5:
                result_text += f"*... and {len(existing_other_groups) - 5} more*\n"
        
        # Show invalid domains (if any)
        if invalid_domains:
            result_text += f"\n**❌ Invalid domains:**\n"
            for domain in invalid_domains[:5]:  # Show first 5
                result_text += f"• `{domain}`\n"
            
            if len(invalid_domains) > 5:
                result_text += f"*... and {len(invalid_domains) - 5} more*\n"
        
        # Create action buttons
        keyboard = [
            [
                InlineKeyboardButton(f"📁 View {group_name}", callback_data=f"group_{group_name}"),
                InlineKeyboardButton("📂 View Groups", callback_data="list_groups")
            ]
        ]
        
        if down_count > 0:
            keyboard.insert(0, [InlineKeyboardButton("🚨 Check Down Domains", callback_data=f"check_group_{group_name}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await status_msg.edit_text(
            result_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        return AUTHENTICATED
    
    async def _add_single_domain(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Add a single domain to monitoring"""
        domain = context.args[0].strip().lower()
        group_name = context.args[1] if len(context.args) > 1 else "Default"
        
        # Basic domain validation
        if not domain or '.' not in domain or len(domain) < 3:
            await update.message.reply_text(
                "❌ **Invalid Domain Format**\n\n"
                "Please provide a valid domain name.\n"
                "**Example:** `example.com`",
                parse_mode='Markdown'
            )
            return AUTHENTICATED
        
        # Send initial message
        status_msg = await update.message.reply_text(
            f"🔄 **Adding domain:** `{domain}`\n"
            f"**Group:** `{group_name}`\n\n"
            "Please wait while I add and perform initial check...",
            parse_mode='Markdown'
        )
        
        if self.db.add_domain(domain, group_name):
            # Perform initial check
            status_data = DomainChecker.check_domain_sync(domain)
            self.db.update_domain_status(domain, status_data)
            
            status_emoji = "✅" if status_data['status'] == 'up' else "🚨"
            response_time_text = f" ({status_data['response_time']:.2f}s)" if status_data['response_time'] else ""
            error_text = f"\n**Error:** `{status_data['error']}`" if status_data['error'] else ""
            
            # Create action buttons
            keyboard = [
                [
                    InlineKeyboardButton("🔍 Check Again", callback_data=f"check_single_{domain}"),
                    InlineKeyboardButton("📋 View Groups", callback_data="list_groups")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await status_msg.edit_text(
                f"✅ **Domain Added Successfully**\n\n"
                f"**Domain:** `{domain}`\n"
                f"**Group:** `{group_name}`\n"
                f"**Status:** {status_emoji} {status_data['status'].upper()}{response_time_text}"
                f"{error_text}",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        else:
            await status_msg.edit_text(
                f"❌ **Failed to Add Domain**\n\n"
                f"Domain `{domain}` is already being monitored or could not be added.",
                parse_mode='Markdown'
            )
        
        return AUTHENTICATED
    
    @require_permission('remove_domains')
    async def remove_domain(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Remove a domain from monitoring"""
        if not context.args:
            await update.message.reply_text(
                "❌ **Missing Domain**\n\n"
                "Please provide a domain to remove.\n"
                "**Usage:** `/remove example.com`",
                parse_mode='Markdown'
            )
            return AUTHENTICATED
        
        domain = context.args[0].strip().lower()
        
        if self.db.remove_domain(domain):
            keyboard = [[InlineKeyboardButton("📋 View Remaining", callback_data="list_domains")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"✅ **Domain Removed**\n\n"
                f"Domain `{domain}` has been removed from monitoring.",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                f"❌ **Domain Not Found**\n\n"
                f"Domain `{domain}` is not in the monitoring list.",
                parse_mode='Markdown'
            )
        
        return AUTHENTICATED
    
    def _create_domain_list_keyboard(self, domains: List[Dict], page: int = 0, group_name: str = None, user_id: int = None) -> InlineKeyboardMarkup:
        """Create paginated keyboard for domain list with group support"""
        keyboard = []
        
        start_idx = page * self.DOMAINS_PER_PAGE
        end_idx = start_idx + self.DOMAINS_PER_PAGE
        page_domains = domains[start_idx:end_idx]
        
        # Check if user can delete domains
        can_delete = self.user_service and user_id and self.user_service.has_permission(user_id, 'remove_domains')
        
        # Add domain buttons
        for domain_doc in page_domains:
            domain = domain_doc['domain']
            status = domain_doc.get('last_status', 'unknown')
            status_emoji = {'up': '✅', 'down': '🚨', 'unknown': '⚪'}.get(status, '⚪')
            
            # Create row buttons
            row_buttons = [
                InlineKeyboardButton(
                    f"{status_emoji} {domain}",
                    callback_data=f"domain_info_{domain}"
                ),
                InlineKeyboardButton("🔄", callback_data=f"check_single_{domain}")
            ]
            
            # Add delete button only if user has permission
            if can_delete:
                row_buttons.append(InlineKeyboardButton("🗑️", callback_data=f"delete_confirm_{domain}"))
            
            keyboard.append(row_buttons)
        
        # Add pagination buttons
        nav_buttons = []
        total_pages = math.ceil(len(domains) / self.DOMAINS_PER_PAGE)
        
        if page > 0:
            callback_data = f"group_page_{group_name}_{page-1}" if group_name else f"list_page_{page-1}"
            nav_buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=callback_data))
        
        nav_buttons.append(InlineKeyboardButton(f"📄 {page+1}/{total_pages}", callback_data="noop"))
        
        if page < total_pages - 1:
            callback_data = f"group_page_{group_name}_{page+1}" if group_name else f"list_page_{page+1}"
            nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=callback_data))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        # Add action buttons
        if group_name:
            keyboard.append([
                InlineKeyboardButton("🔍 Check Group", callback_data=f"check_group_{group_name}"),
                InlineKeyboardButton("🔄 Refresh", callback_data=f"group_{group_name}")
            ])
            keyboard.append([
                InlineKeyboardButton("📂 Back to Groups", callback_data="list_groups"),
                InlineKeyboardButton("🔍 Check All", callback_data="check_all")
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("🔍 Check All", callback_data="check_all"),
                InlineKeyboardButton("🔄 Refresh", callback_data=f"list_page_{page}")
            ])
            keyboard.append([
                InlineKeyboardButton("📂 View by Groups", callback_data="list_groups")
            ])
        
        return InlineKeyboardMarkup(keyboard)
    
    async def list_groups(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show group selection interface"""
        groups = self.db.get_groups()
        group_summary = self.db.get_group_summary()
        
        if not groups or not group_summary:
            keyboard = [[InlineKeyboardButton("➕ Add First Domain", callback_data="help_add")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            text = (
                "📝 **No Groups Found**\n\n"
                "You haven't added any domains yet.\n"
                "Use `/add <domain> [group_name]` to start monitoring."
            )
        else:
            keyboard = []
            text = "📂 **Domain Groups**\n\nSelect a group to view its domains:\n\n"
            
            # Add group buttons with statistics
            for group in groups:
                stats = group_summary.get(group, {'total': 0, 'up': 0, 'down': 0, 'unknown': 0})
                status_text = f"✅{stats['up']} 🚨{stats['down']}"
                if stats['unknown'] > 0:
                    status_text += f" ⚪{stats['unknown']}"
                
                button_text = f"📁 {group} ({stats['total']}) - {status_text}"
                keyboard.append([InlineKeyboardButton(button_text, callback_data=f"group_{group}")])
            
            # Add action buttons
            keyboard.append([
                InlineKeyboardButton("🔍 Check All Groups", callback_data="check_all_groups"),
                InlineKeyboardButton("📊 Group Summary", callback_data="group_summary")
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            try:
                await update.callback_query.edit_message_text(
                    text,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            except Exception as e:
                await update.callback_query.answer("✅ Groups loaded!")
                logger.debug(f"Failed to edit message: {e}")
        else:
            await update.message.reply_text(
                text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        
        return AUTHENTICATED

    async def list_domains(self, update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0, group_name: str = None) -> int:
        """List domains with optional group filtering"""
        if group_name:
            domains = self.db.get_domains_by_group(group_name)
            title = f"📁 Group: {group_name}"
        else:
            domains = self.db.get_all_domains()
            title = "📋 All Domains"
        
        if not domains:
            if group_name:
                keyboard = [
                    [InlineKeyboardButton("📂 Back to Groups", callback_data="list_groups")],
                    [InlineKeyboardButton("➕ Add Domain to Group", callback_data="help_add")]
                ]
                text = f"📝 **No Domains in {group_name}**\n\nThis group is empty.\nUse `/add <domain> {group_name}` to add domains."
            else:
                keyboard = [[InlineKeyboardButton("➕ Add First Domain", callback_data="help_add")]]
                text = "📝 **No Domains Monitored**\n\nYou haven't added any domains yet.\nUse `/add <domain>` to start monitoring."
            
            reply_markup = InlineKeyboardMarkup(keyboard)
        else:
            # Sort domains: down first, then by name
            domains.sort(key=lambda x: (x.get('last_status') != 'down', x['domain']))
            
            user_id = update.effective_user.id
            reply_markup = self._create_domain_list_keyboard(domains, page, group_name, user_id)
            
            # Create summary
            up_count = sum(1 for d in domains if d.get('last_status') == 'up')
            down_count = sum(1 for d in domains if d.get('last_status') == 'down')
            unknown_count = len(domains) - up_count - down_count
            
            # Add timestamp to make content unique for refresh
            current_time = datetime.now().strftime('%H:%M:%S')
            text = (
                f"{title} ({len(domains)} total)\n\n"
                f"✅ **UP:** {up_count} | 🚨 **DOWN:** {down_count} | ⚪ **Unknown:** {unknown_count}\n\n"
                f"*Showing page {page+1} of {math.ceil(len(domains) / self.DOMAINS_PER_PAGE)}*\n"
                f"*Last updated: {current_time}*"
            )
        
        if update.callback_query:
            try:
                await update.callback_query.edit_message_text(
                    text,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            except Exception as e:
                await update.callback_query.answer("✅ List refreshed!")
                logger.debug(f"Failed to edit message: {e}")
        else:
            await update.message.reply_text(
                text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        
        return AUTHENTICATED
    
    async def check_all_domains(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Check all domains and show results"""
        domains = self.db.get_all_domains()
        
        if not domains:
            await update.message.reply_text(
                "📝 **No Domains to Check**\n\n"
                "Add some domains first using `/add <domain>`",
                parse_mode='Markdown'
            )
            return AUTHENTICATED
        
        # Send initial checking message
        if update.callback_query:
            try:
                await update.callback_query.edit_message_text(
                    f"🔄 **Checking {len(domains)} domains...**\n\n"
                    "Using optimized concurrent checking. Please wait...",
                    parse_mode='Markdown'
                )
                message = update.callback_query.message
            except Exception as e:
                await update.callback_query.answer("🔄 Starting domain check...")
                message = update.callback_query.message
                logger.debug(f"Failed to edit check message: {e}")
        else:
            message = await update.message.reply_text(
                f"🔄 **Checking {len(domains)} domains...**\n\n"
                "Using optimized concurrent checking. Please wait...",
                parse_mode='Markdown'
            )
        
        # Check all domains concurrently with optimized performance
        domain_names = [d['domain'] for d in domains]
        results = await DomainChecker.check_multiple_domains(domain_names, max_concurrent=100)
        
        # Bulk update database for better performance
        status_updates = [{'domain': r['domain'], 'status_data': r} for r in results]
        self.db.bulk_update_status(status_updates)
        
        # Generate report
        up_domains = [r for r in results if r['status'] == 'up']
        down_domains = [r for r in results if r['status'] == 'down']
        
        report_text = (
            f"📊 **Domain Check Complete**\n\n"
            f"**Summary:** ✅ {len(up_domains)} UP | 🚨 {len(down_domains)} DOWN\n\n"
        )
        
        # Show down domains first
        if down_domains:
            report_text += "🚨 **DOWN Domains:**\n"
            for result in down_domains[:10]:  # Limit to first 10
                error_text = f" - {result['error']}" if result['error'] else ""
                report_text += f"• `{result['domain']}`{error_text}\n"
            
            if len(down_domains) > 10:
                report_text += f"*... and {len(down_domains) - 10} more*\n"
            report_text += "\n"
        
        # Show some up domains
        if up_domains:
            report_text += "✅ **UP Domains:**\n"
            for result in up_domains[:5]:  # Show first 5
                time_text = f" ({result['response_time']:.2f}s)" if result['response_time'] else ""
                report_text += f"• `{result['domain']}`{time_text}\n"
            
            if len(up_domains) > 5:
                report_text += f"*... and {len(up_domains) - 5} more*\n"
        
        # Create action buttons
        keyboard = [
            [
                InlineKeyboardButton("📂 View by Groups", callback_data="list_groups"),
                InlineKeyboardButton("🔄 Check Again", callback_data="check_all")
            ]
        ]
        
        if down_domains:
            keyboard.insert(0, [InlineKeyboardButton("🚨 Show Down Details", callback_data="show_down_details")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await message.edit_text(
                report_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        except Exception as e:
            # If edit fails, send a new message
            await message.reply_text(
                report_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            logger.debug(f"Failed to edit check result message: {e}")
        
        return AUTHENTICATED

    async def check_group_domains(self, update: Update, context: ContextTypes.DEFAULT_TYPE, group_name: str) -> int:
        """Check all domains in a specific group"""
        domains = self.db.get_domains_by_group(group_name)
        
        if not domains:
            await update.callback_query.edit_message_text(
                f"📝 **No Domains in {group_name}**\n\n"
                f"This group is empty.",
                parse_mode='Markdown'
            )
            return AUTHENTICATED
        
        # Send initial checking message
        try:
            await update.callback_query.edit_message_text(
                f"🔄 **Checking {len(domains)} domains in {group_name}...**\n\n"
                "Please wait...",
                parse_mode='Markdown'
            )
            message = update.callback_query.message
        except Exception as e:
            await update.callback_query.answer("🔄 Starting group check...")
            message = update.callback_query.message
            logger.debug(f"Failed to edit check message: {e}")
        
        # Check group domains concurrently
        domain_names = [d['domain'] for d in domains]
        results = await DomainChecker.check_multiple_domains(domain_names, max_concurrent=50)
        
        # Update database with results
        status_updates = [{'domain': r['domain'], 'status_data': r} for r in results]
        self.db.bulk_update_status(status_updates)
        
        # Generate report
        up_domains = [r for r in results if r['status'] == 'up']
        down_domains = [r for r in results if r['status'] == 'down']
        
        report_text = (
            f"📊 **Group Check Complete: {group_name}**\n\n"
            f"**Summary:** ✅ {len(up_domains)} UP | 🚨 {len(down_domains)} DOWN\n\n"
        )
        
        # Show down domains first
        if down_domains:
            report_text += "🚨 **DOWN Domains:**\n"
            for result in down_domains:
                error_text = f" - {result['error']}" if result['error'] else ""
                report_text += f"• `{result['domain']}`{error_text}\n"
            report_text += "\n"
        
        # Show up domains
        if up_domains:
            report_text += "✅ **UP Domains:**\n"
            for result in up_domains[:10]:  # Show first 10
                time_text = f" ({result['response_time']:.2f}s)" if result['response_time'] else ""
                report_text += f"• `{result['domain']}`{time_text}\n"
            
            if len(up_domains) > 10:
                report_text += f"*... and {len(up_domains) - 10} more*\n"
        
        # Create action buttons
        keyboard = [
            [
                InlineKeyboardButton(f"📁 View {group_name}", callback_data=f"group_{group_name}"),
                InlineKeyboardButton("🔄 Check Again", callback_data=f"check_group_{group_name}")
            ],
            [
                InlineKeyboardButton("📂 Back to Groups", callback_data="list_groups"),
                InlineKeyboardButton("🔍 Check All", callback_data="check_all")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await message.edit_text(
                report_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        except Exception as e:
            await message.reply_text(
                report_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            logger.debug(f"Failed to edit check result message: {e}")
        
        return AUTHENTICATED

    async def check_all_groups(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Check all domains organized by groups"""
        groups = self.db.get_groups()
        
        if not groups:
            await update.callback_query.edit_message_text(
                "📝 **No Groups Found**\n\nAdd some domains first.",
                parse_mode='Markdown'
            )
            return AUTHENTICATED
        
        # Send initial checking message
        total_domains = self.db.get_domains_count()
        try:
            await update.callback_query.edit_message_text(
                f"🔄 **Checking {total_domains} domains across {len(groups)} groups...**\n\n"
                "Using optimized group-based checking. Please wait...",
                parse_mode='Markdown'
            )
            message = update.callback_query.message
        except Exception as e:
            await update.callback_query.answer("🔄 Starting group check...")
            message = update.callback_query.message
            logger.debug(f"Failed to edit check message: {e}")
        
        # Prepare domains by group
        domains_by_group = {}
        for group in groups:
            group_domains = self.db.get_domains_by_group(group)
            domains_by_group[group] = [d['domain'] for d in group_domains]
        
        # Check all groups concurrently
        results_by_group = await DomainChecker.check_domains_by_group(domains_by_group, max_concurrent=100)
        
        # Update database with all results
        all_updates = []
        for group_results in results_by_group.values():
            for result in group_results:
                all_updates.append({'domain': result['domain'], 'status_data': result})
        
        self.db.bulk_update_status(all_updates)
        
        # Generate group summary report
        report_text = f"📊 **All Groups Check Complete**\n\n"
        
        total_up = total_down = 0
        for group_name, results in results_by_group.items():
            up_count = sum(1 for r in results if r['status'] == 'up')
            down_count = sum(1 for r in results if r['status'] == 'down')
            total_up += up_count
            total_down += down_count
            
            status_emoji = "🚨" if down_count > 0 else "✅"
            report_text += f"{status_emoji} **{group_name}:** ✅{up_count} 🚨{down_count}\n"
        
        report_text += f"\n**Overall:** ✅ {total_up} UP | 🚨 {total_down} DOWN"
        
        # Create action buttons
        keyboard = [
            [
                InlineKeyboardButton("📂 View Groups", callback_data="list_groups"),
                InlineKeyboardButton("🔄 Check Again", callback_data="check_all_groups")
            ]
        ]
        
        if total_down > 0:
            keyboard.insert(0, [InlineKeyboardButton("🚨 Show Down Details", callback_data="show_down_details")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await message.edit_text(
                report_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        except Exception as e:
            await message.reply_text(
                report_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            logger.debug(f"Failed to edit check result message: {e}")
        
        return AUTHENTICATED

    async def show_group_summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show detailed group summary"""
        group_summary = self.db.get_group_summary()
        
        if not group_summary:
            await update.callback_query.edit_message_text(
                "📝 **No Groups Found**\n\nAdd some domains first.",
                parse_mode='Markdown'
            )
            return AUTHENTICATED
        
        text = "📊 **Group Summary**\n\n"
        
        total_domains = total_up = total_down = total_unknown = 0
        
        for group_name, stats in sorted(group_summary.items()):
            total_domains += stats['total']
            total_up += stats['up']
            total_down += stats['down']
            total_unknown += stats['unknown']
            
            # Group status indicator
            if stats['down'] > 0:
                status_emoji = "🚨"
            elif stats['up'] == stats['total']:
                status_emoji = "✅"
            else:
                status_emoji = "⚪"
            
            text += (
                f"{status_emoji} **{group_name}** ({stats['total']} domains)\n"
                f"   ✅ UP: {stats['up']} | 🚨 DOWN: {stats['down']}"
            )
            
            if stats['unknown'] > 0:
                text += f" | ⚪ Unknown: {stats['unknown']}"
            
            text += "\n\n"
        
        text += (
            f"**📈 Overall Statistics:**\n"
            f"• Total Domains: {total_domains}\n"
            f"• ✅ UP: {total_up} ({total_up/total_domains*100:.1f}%)\n"
            f"• 🚨 DOWN: {total_down} ({total_down/total_domains*100:.1f}%)\n"
        )
        
        if total_unknown > 0:
            text += f"• ⚪ Unknown: {total_unknown} ({total_unknown/total_domains*100:.1f}%)\n"
        
        keyboard = [
            [
                InlineKeyboardButton("📂 Back to Groups", callback_data="list_groups"),
                InlineKeyboardButton("🔍 Check All", callback_data="check_all_groups")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await update.callback_query.edit_message_text(
                text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        except Exception as e:
            await update.callback_query.answer("✅ Summary loaded!")
            logger.debug(f"Failed to edit message: {e}")
        
        return AUTHENTICATED