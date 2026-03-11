# 🚀 ToonPay Advanced Support Bot

Enterprise-level Telegram support bot for ToonPay with complete ticket management system.

## ✨ Features

### 👤 User Features
- Create support tickets with category selection
- Upload name, email, phone, and issue description
- View personal ticket history
- Receive real-time admin responses
- 24/7 support availability

### 👥 Admin Features
- View all open tickets
- Mark tickets as "In Progress"
- Reply to tickets (closes automatically)
- Close tickets without reply
- Search users by ID, username, email, or phone
- View user statistics and ticket history
- Filter tickets by status
- Export data in CSV/Excel formats

### 👑 Super Admin Features
- Complete control panel
- Add/remove admins
- Add/remove allowed groups
- View system statistics
- Broadcast messages to all users
- Manual and automatic backups
- Export all data
- System settings management

### 🔒 Security Features
- Commands restricted to appropriate groups
- User messages auto-deleted for privacy
- Admin-only access to sensitive data
- Super admin protection
- Database backups

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Telegram Bot Token (from @BotFather)
- Railway account (or any hosting)

### Environment Variables
Create `.env` file:
```env
BOT_TOKEN=your_bot_token
BOT_USERNAME=@your_bot_username
ADMIN_GROUP_ID=-1001234567890
SUPER_ADMIN_IDS=123456789,987654321
DATABASE_URL=postgresql://user:pass@host:port/db
