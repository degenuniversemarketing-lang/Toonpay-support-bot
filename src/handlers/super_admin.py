from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from sqlalchemy import select, func, and_, or_
from database import get_db
from database import AdminGroup, BotCommand, User, Ticket
from utils.decorators import super_admin_only, admin_group_only
from utils.helpers import format_detailed_export, generate_ticket_link
from config import Config
from datetime import datetime, timedelta
import os
import io
import pandas as pd
import asyncio
import logging

logger = logging.getLogger(__name__)
router = Router()

# ==================== SUPER ADMIN PANEL ====================

@router.message(Command("panel"))
@super_admin_only()
async def super_admin_panel(message: Message):
    """Open super admin control panel"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Statistics", callback_data="sa_stats")],
        [InlineKeyboardButton(text="📋 All Tickets", callback_data="sa_tickets")],
        [InlineKeyboardButton(text="👥 Users Management", callback_data="sa_users")],
        [InlineKeyboardButton(text="🔧 System Settings", callback_data="sa_settings")],
        [InlineKeyboardButton(text="📤 Export Data", callback_data="sa_export")],
        [InlineKeyboardButton(text="📢 Broadcast", callback_data="sa_broadcast")],
        [InlineKeyboardButton(text="⚙️ Bot Commands", callback_data="sa_commands")],
        [InlineKeyboardButton(text="🔍 Advanced Search", callback_data="sa_search")],
        [InlineKeyboardButton(text="❌ Close Panel", callback_data="sa_close")]
    ])
    
    await message.answer(
        "👑 <b>Super Admin Control Panel</b>\n\n"
        "Welcome to the master control panel. Select an option below:",
        reply_markup=keyboard
    )

@router.callback_query(F.data.startswith("sa_"))
@super_admin_only()
async def super_admin_callback(callback: CallbackQuery):
    """Handle super admin panel callbacks"""
    action = callback.data.replace("sa_", "")
    
    if action == "stats":
        await show_detailed_stats(callback)
    elif action == "tickets":
        await show_all_tickets_filter(callback)
    elif action == "users":
        await show_users_management(callback)
    elif action == "settings":
        await show_system_settings(callback)
    elif action == "export":
        await show_export_options(callback)
    elif action == "broadcast":
        await show_broadcast_options(callback)
    elif action == "commands":
        await show_commands_manager(callback)
    elif action == "search":
        await show_advanced_search(callback)
    elif action == "close":
        await callback.message.delete()
        await callback.answer("Panel closed")

async def show_detailed_stats(callback: CallbackQuery):
    """Show detailed statistics"""
    async for session in get_db():
        # Get counts
        users_count = await session.scalar(select(func.count(User.id)))
        tickets_count = await session.scalar(select(func.count(Ticket.id)))
        
        # Get tickets by status
        open_tickets = await session.scalar(
            select(func.count(Ticket.id)).where(Ticket.status == 'open')
        )
        progress_tickets = await session.scalar(
            select(func.count(Ticket.id)).where(Ticket.status == 'in_progress')
        )
        replied_closed = await session.scalar(
            select(func.count(Ticket.id)).where(and_(Ticket.status == 'closed', Ticket.admin_answer.isnot(None)))
        )
        closed_no_reply = await session.scalar(
            select(func.count(Ticket.id)).where(and_(Ticket.status == 'closed', Ticket.admin_answer.is_(None)))
        )
        
        # Get today's tickets
        today = datetime.utcnow().date()
        today_tickets = await session.scalar(
            select(func.count(Ticket.id)).where(
                func.date(Ticket.created_at) == today
            )
        )
        
        # Get active groups
        active_groups = await session.scalar(
            select(func.count(AdminGroup.id)).where(AdminGroup.is_active == True)
        )
        
        stats_message = f"""
<b>📊 Detailed Statistics</b>

<b>👥 Users:</b>
• Total Users: {users_count or 0}

<b>🎫 Tickets Overview:</b>
• Total Tickets: {tickets_count or 0}
• 🟢 Open: {open_tickets or 0}
• 🟡 In Progress: {progress_tickets or 0}
• ✅ Replied & Closed: {replied_closed or 0}
• 🔴 Closed No Reply: {closed_no_reply or 0}

<b>📈 Performance:</b>
• Response Rate: {((replied_closed or 0) / (tickets_count or 1) * 100):.1f}%
• 📅 Today's Tickets: {today_tickets or 0}

<b>⚙️ Settings:</b>
• Active Groups: {active_groups or 0}
• Admin Group: {Config.ADMIN_GROUP_ID}
"""
        await callback.message.edit_text(stats_message)
        await callback.answer()

async def show_all_tickets_filter(callback: CallbackQuery):
    """Show tickets with filters"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Open Tickets", callback_data="sa_filter_open")],
        [InlineKeyboardButton(text="🟡 In Progress", callback_data="sa_filter_progress")],
        [InlineKeyboardButton(text="✅ Replied & Closed", callback_data="sa_filter_replied")],
        [InlineKeyboardButton(text="🔴 Closed No Reply", callback_data="sa_filter_closed")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="sa_stats")]
    ])
    
    await callback.message.edit_text(
        "📋 <b>Select Ticket Filter:</b>",
        reply_markup=keyboard
    )
    await callback.answer()

async def show_users_management(callback: CallbackQuery):
    """Show user management options"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 User Statistics", callback_data="sa_user_stats")],
        [InlineKeyboardButton(text="🔍 Search User", callback_data="sa_user_search")],
        [InlineKeyboardButton(text="📤 Export Users", callback_data="sa_export_users")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="sa_stats")]
    ])
    
    await callback.message.edit_text(
        "👥 <b>User Management</b>\n\n"
        "Select an option:",
        reply_markup=keyboard
    )
    await callback.answer()

async def show_system_settings(callback: CallbackQuery):
    """Show system settings"""
    async for session in get_db():
        groups_count = await session.scalar(
            select(func.count(AdminGroup.id)).where(AdminGroup.is_active == True)
        )
        commands_count = await session.scalar(select(func.count(BotCommand.id)))
        
        settings_text = f"""
<b>🔧 System Settings</b>

<b>Current Configuration:</b>
• Bot Token: {Config.BOT_TOKEN[:10]}...{Config.BOT_TOKEN[-5:]}
• Super Admin ID: {Config.SUPER_ADMIN_ID}
• Admin Group ID: {Config.ADMIN_GROUP_ID}

<b>Database Stats:</b>
• Active Groups: {groups_count or 0}
• Custom Commands: {commands_count or 0}

Use these commands to manage settings:
/addgroup - Add a new group
/removegroup - Remove a group
/listgroups - List all groups
/editcmd - Edit bot commands
"""
        await callback.message.edit_text(settings_text)
        await callback.answer()

async def show_export_options(callback: CallbackQuery):
    """Show export options"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Complete Export", callback_data="sa_export_all")],
        [InlineKeyboardButton(text="👥 Users Only", callback_data="sa_export_users")],
        [InlineKeyboardButton(text="🎫 Tickets Only", callback_data="sa_export_tickets")],
        [InlineKeyboardButton(text="📅 Last 30 Days", callback_data="sa_export_30d")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="sa_stats")]
    ])
    
    await callback.message.edit_text(
        "📤 <b>Export Options</b>\n\n"
        "Select the data you want to export:",
        reply_markup=keyboard
    )
    await callback.answer()

async def show_broadcast_options(callback: CallbackQuery):
    """Show broadcast options"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Broadcast to All", callback_data="sa_broadcast_all")],
        [InlineKeyboardButton(text="👥 Broadcast to Users", callback_data="sa_broadcast_users")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="sa_stats")]
    ])
    
    await callback.message.edit_text(
        "📢 <b>Broadcast Message</b>\n\n"
        "Select broadcast type:",
        reply_markup=keyboard
    )
    await callback.answer()

async def show_commands_manager(callback: CallbackQuery):
    """Show commands manager"""
    async for session in get_db():
        commands = await session.execute(select(BotCommand))
        commands = commands.scalars().all()
        
        text = "<b>⚙️ Bot Commands</b>\n\n"
        if commands:
            for cmd in commands:
                text += f"• /{cmd.command} - {cmd.response_text[:50]}...\n"
        else:
            text += "No custom commands yet.\n"
        
        text += "\nUse /editcmd command|response to add/edit commands"
        
        await callback.message.edit_text(text)
        await callback.answer()

async def show_advanced_search(callback: CallbackQuery):
    """Show advanced search options"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Search by User ID", callback_data="sa_search_id")],
        [InlineKeyboardButton(text="🔍 Search by Username", callback_data="sa_search_username")],
        [InlineKeyboardButton(text="🔍 Search by Email", callback_data="sa_search_email")],
        [InlineKeyboardButton(text="🔍 Search by Phone", callback_data="sa_search_phone")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="sa_stats")]
    ])
    
    await callback.message.edit_text(
        "🔍 <b>Advanced Search</b>\n\n"
        "Select search type:",
        reply_markup=keyboard
    )
    await callback.answer()

# ==================== ENHANCED DATA EXPORT ====================

@router.message(Command("data"))
@admin_group_only()
async def get_filtered_data(message: Message):
    """Get filtered data with options - Works in admin group only"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Complete Export", callback_data="export_all")],
        [InlineKeyboardButton(text="🟢 Open Tickets", callback_data="export_open")],
        [InlineKeyboardButton(text="🟡 In Progress", callback_data="export_progress")],
        [InlineKeyboardButton(text="✅ Replied & Closed", callback_data="export_replied")],
        [InlineKeyboardButton(text="🔴 Closed No Reply", callback_data="export_closed_noreply")],
        [InlineKeyboardButton(text="📅 Last 24 Hours", callback_data="export_24h")],
        [InlineKeyboardButton(text="📅 Last 7 Days", callback_data="export_7d")],
        [InlineKeyboardButton(text="📅 Custom Range", callback_data="export_custom")]
    ])
    
    await message.reply(
        "📤 <b>Data Export Options</b>\n\n"
        "Select the type of data you want to export:",
        reply_markup=keyboard
    )

@router.callback_query(F.data.startswith("export_"))
@admin_group_only()
async def export_callback(callback: CallbackQuery):
    """Handle export callbacks"""
    export_type = callback.data.replace("export_", "")
    
    await callback.message.edit_text("📊 Generating export...")
    
    async for session in get_db():
        # Build query based on export type
        if export_type == "all":
            tickets_result = await session.execute(select(Ticket))
        elif export_type == "open":
            tickets_result = await session.execute(select(Ticket).where(Ticket.status == 'open'))
        elif export_type == "progress":
            tickets_result = await session.execute(select(Ticket).where(Ticket.status == 'in_progress'))
        elif export_type == "replied":
            tickets_result = await session.execute(
                select(Ticket).where(and_(Ticket.status == 'closed', Ticket.admin_answer.isnot(None)))
            )
        elif export_type == "closed_noreply":
            tickets_result = await session.execute(
                select(Ticket).where(and_(Ticket.status == 'closed', Ticket.admin_answer.is_(None)))
            )
        elif export_type == "24h":
            since = datetime.utcnow() - timedelta(hours=24)
            tickets_result = await session.execute(
                select(Ticket).where(Ticket.created_at >= since)
            )
        elif export_type == "7d":
            since = datetime.utcnow() - timedelta(days=7)
            tickets_result = await session.execute(
                select(Ticket).where(Ticket.created_at >= since)
            )
        else:
            tickets_result = await session.execute(select(Ticket))
        
        tickets = tickets_result.scalars().all()
        
        # Create export data
        export_data = []
        for ticket in tickets:
            # Get user info
            user_result = await session.execute(
                select(User).where(User.telegram_id == ticket.user_id)
            )
            user = user_result.scalar_one_or_none()
            
            export_data.append({
                'Ticket ID': ticket.ticket_id,
                'User ID': ticket.user_id,
                'Username': user.username if user else 'N/A',
                'User Name': user.first_name if user else ticket.user_name,
                'Email': ticket.email,
                'Phone': ticket.phone,
                'Category': ticket.category,
                'Status': ticket.status,
                'Created': ticket.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'Description': ticket.description,
                'Admin Answer': ticket.admin_answer or '',
                'Answered By': ticket.answered_by,
                'Answered At': ticket.answered_at.strftime('%Y-%m-%d %H:%M:%S') if ticket.answered_at else '',
                'In Progress By': ticket.in_progress_by
            })
        
        # Create DataFrame
        df = pd.DataFrame(export_data)
        
        # Save to file
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Tickets', index=False)
        
        output.seek(0)
        
        # Send file
        filename = f'toonpay_export_{export_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        with open(filename, 'wb') as f:
            f.write(output.getvalue())
        
        await callback.message.reply_document(
            FSInputFile(filename),
            caption=f"✅ Export completed: {len(export_data)} tickets"
        )
        
        # Clean up
        os.remove(filename)
        await callback.message.delete()

@router.message(Command("getdata"))
@admin_group_only()
async def enhanced_get_data(message: Message):
    """Enhanced data export with detailed user-ticket structure"""
    await message.reply("📊 Generating detailed export...")
    
    async for session in get_db():
        # Get all users with their tickets
        users_result = await session.execute(
            select(User).order_by(User.registered_at)
        )
        users = users_result.scalars().all()
        
        # Create detailed export
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Detailed Users Sheet
            users_data = []
            for user in users:
                # Get all tickets for this user
                tickets_result = await session.execute(
                    select(Ticket).where(Ticket.user_id == user.telegram_id).order_by(Ticket.created_at)
                )
                tickets = tickets_result.scalars().all()
                
                # User summary row
                users_data.append({
                    'User ID': user.telegram_id,
                    'Username': f"@{user.username}" if user.username else 'N/A',
                    'Full Name': f"{user.first_name} {user.last_name or ''}".strip(),
                    'Email': user.email or 'Not provided',
                    'Phone': user.phone or 'Not provided',
                    'Registered': user.registered_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'Total Tickets': len(tickets),
                    'Open Tickets': sum(1 for t in tickets if t.status == 'open'),
                    'In Progress': sum(1 for t in tickets if t.status == 'in_progress'),
                    'Replied & Closed': sum(1 for t in tickets if t.status == 'closed' and t.admin_answer is not None),
                    'Closed No Reply': sum(1 for t in tickets if t.status == 'closed' and t.admin_answer is None)
                })
                
                # Add each ticket as a separate row with user details repeated
                for ticket in tickets:
                    ticket_status = '🟢 Open'
                    if ticket.status == 'in_progress':
                        ticket_status = '🟡 In Progress'
                    elif ticket.status == 'closed':
                        if ticket.admin_answer:
                            ticket_status = '✅ Replied & Closed'
                        else:
                            ticket_status = '🔴 Closed No Reply'
                    
                    users_data.append({
                        'User ID': user.telegram_id,
                        'Username': f"@{user.username}" if user.username else 'N/A',
                        'Full Name': f"{user.first_name} {user.last_name or ''}".strip(),
                        'Email': ticket.email or user.email or 'Not provided',
                        'Phone': ticket.phone or user.phone or 'Not provided',
                        'Ticket ID': ticket.ticket_id,
                        'Category': ticket.category,
                        'Status': ticket_status,
                        'Created': ticket.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'User Question': ticket.description,
                        'Admin Answer': ticket.admin_answer or 'No reply yet',
                        'Answered By': f"Admin {ticket.answered_by}" if ticket.answered_by else 'N/A',
                        'Answered At': ticket.answered_at.strftime('%Y-%m-%d %H:%M:%S') if ticket.answered_at else 'N/A',
                        'In Progress By': f"Admin {ticket.in_progress_by}" if ticket.in_progress_by else 'N/A'
                    })
            
            # Create DataFrames
            df_detailed = pd.DataFrame(users_data)
            
            # Write to Excel
            df_detailed.to_excel(writer, sheet_name='Detailed Report', index=False)
            
            # Summary Sheet
            total_tickets = await session.scalar(select(func.count(Ticket.id)))
            replied_tickets = await session.scalar(select(func.count(Ticket.id)).where(Ticket.admin_answer.isnot(None)))
            
            summary_data = {
                'Metric': [
                    'Total Users',
                    'Total Tickets',
                    'Open Tickets',
                    'In Progress',
                    'Replied & Closed',
                    'Closed No Reply',
                    'Response Rate'
                ],
                'Value': [
                    len(users),
                    total_tickets or 0,
                    await session.scalar(select(func.count(Ticket.id)).where(Ticket.status == 'open')) or 0,
                    await session.scalar(select(func.count(Ticket.id)).where(Ticket.status == 'in_progress')) or 0,
                    await session.scalar(select(func.count(Ticket.id)).where(and_(Ticket.status == 'closed', Ticket.admin_answer.isnot(None)))) or 0,
                    await session.scalar(select(func.count(Ticket.id)).where(and_(Ticket.status == 'closed', Ticket.admin_answer.is_(None)))) or 0,
                    f"{(replied_tickets or 0) / (total_tickets or 1) * 100:.1f}%"
                ]
            }
            df_summary = pd.DataFrame(summary_data)
            df_summary.to_excel(writer, sheet_name='Summary', index=False)
        
        output.seek(0)
        
        # Save temporarily
        filename = f'toonpay_detailed_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        with open(filename, 'wb') as f:
            f.write(output.getvalue())
        
        await message.reply_document(
            FSInputFile(filename),
            caption="✅ Complete detailed export with user-wise ticket history"
        )
        
        # Clean up
        os.remove(filename)

# ==================== GROUP MANAGEMENT ====================

@router.message(Command("addgroup"))
@super_admin_only()
async def add_group(message: Message):
    """Add group to activated groups"""
    try:
        parts = message.text.split()
        if len(parts) != 2:
            await message.reply("❌ Invalid format. Use: /addgroup <group_id>")
            return
            
        group_id = int(parts[1])
        
        async for session in get_db():
            # Check if group exists
            result = await session.execute(
                select(AdminGroup).where(AdminGroup.group_id == group_id)
            )
            group = result.scalar_one_or_none()
            
            if group:
                group.is_active = True
                group.added_by = message.from_user.id
            else:
                group = AdminGroup(
                    group_id=group_id,
                    group_name=f"Group_{group_id}",
                    added_by=message.from_user.id,
                    is_active=True
                )
                session.add(group)
            
            await session.commit()
            
        await message.reply(f"✅ Group {group_id} has been activated for support commands")
    except ValueError:
        await message.reply("❌ Invalid group ID. Must be a number.")
    except Exception as e:
        logger.error(f"Error adding group: {e}")
        await message.reply(f"❌ Error: {str(e)}")

@router.message(Command("removegroup"))
@super_admin_only()
async def remove_group(message: Message):
    """Remove group from activated groups"""
    try:
        parts = message.text.split()
        if len(parts) != 2:
            await message.reply("❌ Invalid format. Use: /removegroup <group_id>")
            return
            
        group_id = int(parts[1])
        
        async for session in get_db():
            result = await session.execute(
                select(AdminGroup).where(AdminGroup.group_id == group_id)
            )
            group = result.scalar_one_or_none()
            
            if group:
                group.is_active = False
                await session.commit()
                await message.reply(f"✅ Group {group_id} has been deactivated")
            else:
                await message.reply("❌ Group not found")
    except ValueError:
        await message.reply("❌ Invalid group ID. Must be a number.")
    except Exception as e:
        logger.error(f"Error removing group: {e}")
        await message.reply(f"❌ Error: {str(e)}")

@router.message(Command("listgroups"))
@super_admin_only()
async def list_groups(message: Message):
    """List all activated groups"""
    async for session in get_db():
        result = await session.execute(
            select(AdminGroup).where(AdminGroup.is_active == True)
        )
        groups = result.scalars().all()
        
        if not groups:
            await message.reply("📭 No active groups")
            return
        
        response = "<b>📋 Active Groups:</b>\n\n"
        for group in groups:
            response += f"• <code>{group.group_id}</code> - {group.group_name}\n"
            response += f"  Added: {group.added_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        
        await message.reply(response)

# ==================== COMMAND MANAGEMENT ====================

@router.message(Command("editcmd"))
@super_admin_only()
async def edit_command(message: Message):
    """Edit bot command responses"""
    # Format: /editcmd command|new response
    try:
        text = message.text.replace("/editcmd", "").strip()
        parts = text.split("|")
        if len(parts) != 2:
            await message.reply("❌ Invalid format. Use: /editcmd command|new response")
            return
        
        command, response = parts[0].strip(), parts[1].strip()
        
        async for session in get_db():
            result = await session.execute(
                select(BotCommand).where(BotCommand.command == command)
            )
            cmd = result.scalar_one_or_none()
            
            if cmd:
                cmd.response_text = response
                cmd.updated_by = message.from_user.id
                cmd.updated_at = datetime.utcnow()
            else:
                cmd = BotCommand(
                    command=command,
                    response_text=response,
                    updated_by=message.from_user.id
                )
                session.add(cmd)
            
            await session.commit()
            
        await message.reply(f"✅ Command '{command}' updated successfully")
    except Exception as e:
        logger.error(f"Error editing command: {e}")
        await message.reply(f"❌ Error: {str(e)}")

# ==================== STATISTICS ====================

@router.message(Command("stats"))
@admin_group_only()
async def enhanced_statistics(message: Message):
    """Enhanced statistics with filters"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 General Stats", callback_data="stats_general")],
        [InlineKeyboardButton(text="🟢 Open Tickets", callback_data="stats_open")],
        [InlineKeyboardButton(text="🟡 In Progress", callback_data="stats_progress")],
        [InlineKeyboardButton(text="✅ Replied & Closed", callback_data="stats_replied")],
        [InlineKeyboardButton(text="🔴 Closed No Reply", callback_data="stats_closed_noreply")],
        [InlineKeyboardButton(text="📅 Last 24 Hours", callback_data="stats_24h")],
        [InlineKeyboardButton(text="📅 This Week", callback_data="stats_week")],
        [InlineKeyboardButton(text="📅 This Month", callback_data="stats_month")]
    ])
    
    await message.reply(
        "📊 <b>Statistics Filters</b>\n\n"
        "Select the statistics you want to view:",
        reply_markup=keyboard
    )

@router.callback_query(F.data.startswith("stats_"))
@admin_group_only()
async def stats_callback(callback: CallbackQuery):
    """Handle statistics filters"""
    filter_type = callback.data.replace("stats_", "")
    
    async for session in get_db():
        if filter_type == "general":
            # General stats
            total = await session.scalar(select(func.count(Ticket.id)))
            open_t = await session.scalar(select(func.count(Ticket.id)).where(Ticket.status == 'open'))
            progress = await session.scalar(select(func.count(Ticket.id)).where(Ticket.status == 'in_progress'))
            replied = await session.scalar(select(func.count(Ticket.id)).where(and_(Ticket.status == 'closed', Ticket.admin_answer.isnot(None))))
            closed_no = await session.scalar(select(func.count(Ticket.id)).where(and_(Ticket.status == 'closed', Ticket.admin_answer.is_(None))))
            users_count = await session.scalar(select(func.count(User.id)))
            
            stats_text = f"""
<b>📊 General Statistics</b>

<b>👥 Users:</b>
• Total Users: {users_count or 0}

<b>🎫 Tickets Overview:</b>
• Total Tickets: {total or 0}
• 🟢 Open: {open_t or 0}
• 🟡 In Progress: {progress or 0}
• ✅ Replied & Closed: {replied or 0}
• 🔴 Closed No Reply: {closed_no or 0}

<b>📈 Performance:</b>
• Response Rate: {((replied or 0) / (total or 1) * 100):.1f}%
            """
            
        elif filter_type == "open":
            tickets = await session.execute(
                select(Ticket).where(Ticket.status == 'open').order_by(Ticket.created_at.desc())
            )
            tickets = tickets.scalars().all()
            stats_text = f"<b>🟢 Open Tickets: {len(tickets)}</b>\n\n"
            for t in tickets[:10]:
                stats_text += f"• <code>{t.ticket_id}</code> - {t.category}\n  From: {t.name}\n  Created: {t.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        
        elif filter_type == "progress":
            tickets = await session.execute(
                select(Ticket).where(Ticket.status == 'in_progress').order_by(Ticket.created_at.desc())
            )
            tickets = tickets.scalars().all()
            stats_text = f"<b>🟡 In Progress Tickets: {len(tickets)}</b>\n\n"
            for t in tickets[:10]:
                stats_text += f"• <code>{t.ticket_id}</code> - {t.category}\n  From: {t.name}\n  In Progress by: Admin {t.in_progress_by}\n  Created: {t.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        
        elif filter_type == "replied":
            tickets = await session.execute(
                select(Ticket).where(and_(Ticket.status == 'closed', Ticket.admin_answer.isnot(None))).order_by(Ticket.answered_at.desc())
            )
            tickets = tickets.scalars().all()
            stats_text = f"<b>✅ Replied & Closed Tickets: {len(tickets)}</b>\n\n"
            for t in tickets[:10]:
                stats_text += f"• <code>{t.ticket_id}</code> - {t.category}\n  Replied by: Admin {t.answered_by}\n  Reply: {t.admin_answer[:50]}...\n\n"
        
        elif filter_type == "closed_noreply":
            tickets = await session.execute(
                select(Ticket).where(and_(Ticket.status == 'closed', Ticket.admin_answer.is_(None))).order_by(Ticket.answered_at.desc())
            )
            tickets = tickets.scalars().all()
            stats_text = f"<b>🔴 Closed Without Reply: {len(tickets)}</b>\n\n"
            for t in tickets[:10]:
                stats_text += f"• <code>{t.ticket_id}</code> - {t.category}\n  Closed by: Admin {t.answered_by}\n  Created: {t.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        
        elif filter_type == "24h":
            since = datetime.utcnow() - timedelta(hours=24)
            tickets = await session.execute(
                select(Ticket).where(Ticket.created_at >= since).order_by(Ticket.created_at.desc())
            )
            tickets = tickets.scalars().all()
            stats_text = f"<b>📅 Last 24 Hours: {len(tickets)} Tickets</b>\n\n"
            for t in tickets[:10]:
                status = '🟢' if t.status == 'open' else '🟡' if t.status == 'in_progress' else '🔴'
                stats_text += f"{status} <code>{t.ticket_id}</code> - {t.category}\n  From: {t.name}\n  Created: {t.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        
        elif filter_type == "week":
            since = datetime.utcnow() - timedelta(days=7)
            tickets = await session.execute(
                select(Ticket).where(Ticket.created_at >= since).order_by(Ticket.created_at.desc())
            )
            tickets = tickets.scalars().all()
            stats_text = f"<b>📅 This Week: {len(tickets)} Tickets</b>\n\n"
            for t in tickets[:10]:
                status = '🟢' if t.status == 'open' else '🟡' if t.status == 'in_progress' else '🔴'
                stats_text += f"{status} <code>{t.ticket_id}</code> - {t.category}\n  From: {t.name}\n  Created: {t.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        
        elif filter_type == "month":
            since = datetime.utcnow() - timedelta(days=30)
            tickets = await session.execute(
                select(Ticket).where(Ticket.created_at >= since).order_by(Ticket.created_at.desc())
            )
            tickets = tickets.scalars().all()
            stats_text = f"<b>📅 This Month: {len(tickets)} Tickets</b>\n\n"
            for t in tickets[:10]:
                status = '🟢' if t.status == 'open' else '🟡' if t.status == 'in_progress' else '🔴'
                stats_text += f"{status} <code>{t.ticket_id}</code> - {t.category}\n  From: {t.name}\n  Created: {t.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        
        else:
            stats_text = "Invalid filter"
        
        await callback.message.edit_text(stats_text)
        await callback.answer()

# ==================== BROADCAST ====================

@router.message(Command("broadcast"))
@super_admin_only()
async def broadcast_message(message: Message):
    """Broadcast message to all users"""
    text = message.text.replace("/broadcast", "").strip()
    
    if not text:
        await message.reply("❌ Usage: /broadcast <message>")
        return
    
    await message.reply("📨 Broadcasting message to all users...")
    
    async for session in get_db():
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        success = 0
        failed = 0
        
        for user in users:
            try:
                await message.bot.send_message(
                    user.telegram_id,
                    f"📢 <b>Announcement:</b>\n\n{text}\n\n⏱️ ToonPay Support Available 24/7"
                )
                success += 1
                await asyncio.sleep(0.05)  # Small delay to avoid flooding
            except Exception as e:
                logger.error(f"Failed to send to {user.telegram_id}: {e}")
                failed += 1
        
        await message.reply(f"✅ Broadcast completed!\n✓ Sent: {success}\n✗ Failed: {failed}")
