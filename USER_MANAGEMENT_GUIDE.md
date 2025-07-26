# 👥 User Management Guide

## Overview

The Telegram Domain Checker Bot now supports role-based access control with three user roles:

- **👑 Admin**: Full access to all features
- **👤 User**: Read-only access to all domains  
- **👥 Guest**: Limited access to assigned groups

## Getting Started

### 1. Adding Your First User (Admin Only)

```bash
# Add a regular user
/adduser 123456789 john_doe user

# Add an admin user
/adduser 987654321 jane_admin admin

# Add a guest user (limited access)
/adduser 555666777 guest_user guest
```

### 2. Finding User IDs

To add users, you need their Telegram User ID:

1. **Method 1**: Ask user to send any message to the bot, check logs
2. **Method 2**: Use @userinfobot - user forwards a message to get their ID
3. **Method 3**: Use @username_to_id_bot

### 3. Managing Users

```bash
# List all users
/listusers

# Remove a user
/removeuser 123456789

# Check your own info
/userinfo
```

## User Roles & Permissions

### 👑 Admin Permissions
- ✅ Add/remove domains
- ✅ Bulk domain operations
- ✅ Manage users (add/remove/list)
- ✅ Access all groups
- ✅ System settings
- ✅ View all statistics

### 👤 User Permissions  
- ✅ View all domains
- ✅ Check domain status
- ✅ Access all groups
- ❌ Add/remove domains
- ❌ Manage users
- ❌ Bulk operations

### 👥 Guest Permissions
- ✅ View assigned groups only
- ✅ Check domain status
- ❌ Add/remove domains
- ❌ Manage users
- ❌ Access other groups
- ❌ Bulk operations

## User Interface Changes

### Role-Specific Menus

Each role sees different options in the main menu:

**Admin Menu:**
- 📂 View Groups
- 🔍 Check All
- 📋 All Domains
- 📊 Group Summary
- 👥 Manage Users ← New!
- ⚙️ Settings ← New!
- ❓ Help
- 🚪 Logout

**User/Guest Menu:**
- 📂 View Groups
- 🔍 Check All
- 📋 All Domains
- 📊 Group Summary
- ❓ Help
- 🚪 Logout

### Permission Checks

The bot automatically checks permissions for each action:
- Commands show "Access Denied" if user lacks permission
- Buttons are hidden/disabled for unauthorized actions
- Error messages explain required permission level

## Advanced Features

### Group-Based Access (Guests)

Guests can be assigned to specific groups:

```bash
# This feature is planned for future updates
# Guests will only see domains in their assigned groups
```

### User Activity Tracking

The system tracks:
- When users were added
- Last activity timestamp
- Who added/removed users
- Role change history

### Bulk User Management

For large deployments:

```bash
# Add multiple users (planned feature)
# Import from CSV file
# Bulk role changes
```

## Security Features

### Access Control
- Only admins can manage users
- Users cannot escalate their own permissions
- All user actions are logged
- Failed access attempts are recorded

### Audit Trail
- User addition/removal is logged
- Permission changes are tracked
- Admin actions are recorded with timestamps

## Troubleshooting

### Common Issues

1. **"Access Denied" errors**
   - Check user role with `/userinfo`
   - Verify user is in database with `/listusers` (admin only)
   - Contact admin to update permissions

2. **User not found**
   - Verify User ID is correct
   - Check if user was removed
   - Re-add user if necessary

3. **Permission errors**
   - Each role has specific permissions
   - Users cannot perform admin actions
   - Guests have very limited access

### Admin Commands for Troubleshooting

```bash
# Check all users
/listusers

# View user statistics
# Use "👥 Manage Users" → "📊 User Stats" in bot menu

# Check system status
# Use "⚙️ Settings" in admin menu
```

## Migration from Old System

### Automatic Admin Migration
- Existing admins (from ADMIN_CHAT_IDS) are automatically added as Admin users
- No action required for existing admins
- Old authentication still works alongside new system

### Adding Existing Users
If you had users before this update:
1. Get their User IDs from chat logs
2. Add them with appropriate roles using `/adduser`
3. Test their access with different commands

## Best Practices

### Role Assignment
- **Admins**: Only trusted users who need full control
- **Users**: Team members who need to monitor domains
- **Guests**: External users or limited access scenarios

### Security
- Regularly review user list with `/listusers`
- Remove inactive users
- Use least privilege principle (start with User role, upgrade if needed)
- Monitor logs for unauthorized access attempts

### User Onboarding
1. Add user with appropriate role
2. Send them bot link and `/start` command
3. Explain their permissions and available commands
4. Provide relevant documentation

## Future Enhancements

Planned features:
- Group-specific guest access
- Bulk user import/export
- User activity dashboard
- Advanced permission granularity
- User self-service features

---

**Need Help?**
- Use `/help` in the bot for interactive help
- Contact your bot administrator
- Check the main deployment guide for technical issues