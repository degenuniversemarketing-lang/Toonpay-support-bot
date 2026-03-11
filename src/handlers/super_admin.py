from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from sqlalchemy import select, func, and_, or_
from database import get_db
from database import AdminGroup, BotCommand, User, Ticket
from utils.decorators import super_admin_only, admin_group_only
from utils.helpers import generate_ticket_link
from config import Config
from datetime import datetime, timedelta
import os
import io
import pandas as pd
import asyncio
import logging

logger = logging.getLogger(__name__)
router = Router()

# ==================== DATA EXPORT COMMANDS ====================

@router.message(Command("data"))
@admin_group_only()
async def data_export_command(message: Message):
    """Data export command with filters - WORKING VERSION"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Complete Export", callback_data="export_all")],
        [InlineKeyboardButton(text="🟢 Open Tickets", callback_data="export_open")],
        [InlineKeyboardButton(text="🟡 In Progress", callback_data="export_progress")],
        [InlineKeyboardButton(text="✅ Replied & Closed", callback_data="export_replied")],
        [InlineKeyboardButton(text="🔴 Closed No Reply", callback_data="export_closed_noreply")],
        [InlineKeyboardButton(text="📅 Last 24 Hours", callback_data="export_24h")],
        [InlineKeyboardButton(text="📅 Last 7 Days", callback_data="export_7d")],
        [InlineKeyboardButton(text="📅 This Month", callback_data="export_month")]
    ])
    
    await message.reply(
        "📤 <b>Data Export Options</b>\n\n"
        "Select the type of data you want to export:",
        reply_markup=keyboard
    )

@router.message(Command("getdata"))
@admin_group_only()
async def getdata_command(message: Message):
    """Enhanced detailed data export - WORKING VERSION"""
    await message.reply("📊 Generating detailed export...")
    
    async for session in get_db():
        try:
            # Get all users
            users_result = await session.execute(
                select(User).order_by(User.registered_at)
            )
            users = users_result.scalars().all()
            
            # Create detailed export
            output = io.BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Detailed data list
                all_data = []
                
                for user in users:
                    # Get user's tickets
                    tickets_result = await session.execute(
                        select(Ticket).where(Ticket.user_id == user.telegram_id).order_by(Ticket.created_at)
                    )
                    tickets = tickets_result.scalars().all()
                    
                    if tickets:
                        # Add each ticket as a row
                        for ticket in tickets:
                            status_text = 'Open'
                            if ticket.status == 'in_progress':
                                status_text = 'In Progress'
                            elif ticket.status == 'closed':
                                status_text = 'Replied & Closed' if ticket.admin_answer else 'Closed No Reply'
                            
                            all_data.append({
                                'User ID': user.telegram_id,
                                'Username': f"@{user.username}" if user.username else 'N/A',
                                'User Full Name': f"{user.first_name} {user.last_name or ''}".strip(),
                                'User Email': user.email or 'Not provided',
                                'User Phone': user.phone or 'Not provided',
                                'Registered Date': user.registered_at.strftime('%Y-%m-%d %H:%M:%S'),
                                'Ticket ID': ticket.ticket_id,
                                'Category': ticket.category,
                                'Status': status_text,
                                'Created Date': ticket.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                                'User Question': ticket.description,
                                'Admin Answer': ticket.admin_answer or 'No reply',
                                'Answered By': ticket.answered_by if ticket.answered_by else 'N/A',
                                'Answered Date': ticket.answered_at.strftime('%Y-%m-%d %H:%M:%S') if ticket.answered_at else 'N/A',
                                'In Progress By': ticket.in_progress_by if ticket.in_progress_by else 'N/A'
                            })
                    else:
                        # User with no tickets
                        all_data.append({
                            'User ID': user.telegram_id,
                            'Username': f"@{user.username}" if user.username else 'N/A',
                            'User Full Name': f"{user.first_name} {user.last_name or ''}".strip(),
                            'User Email': user.email or 'Not provided',
                            'User Phone': user.phone or 'Not provided',
                            'Registered Date': user.registered_at.strftime('%Y-%m-%d %H:%M:%S'),
                            'Ticket ID': 'No tickets',
                            'Category': 'N/A',
                            'Status': 'N/A',
                            'Created Date': 'N/A',
                            'User Question': 'N/A',
                            'Admin Answer': 'N/A',
                            'Answered By': 'N/A',
                            'Answered Date': 'N/A',
                            'In Progress By': 'N/A'
                        })
                
                # Create DataFrame
                df = pd.DataFrame(all_data)
                df.to_excel(writer, sheet_name='Detailed Report', index=False)
                
                # Summary Sheet
                total_tickets = await session.scalar(select(func.count(Ticket.id))) or 0
                replied_tickets = await session.scalar(
                    select(func.count(Ticket.id)).where(Ticket.admin_answer.isnot(None))
                ) or 0
                
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
                        total_tickets,
                        await session.scalar(select(func.count(Ticket.id)).where(Ticket.status == 'open')) or 0,
                        await session.scalar(select(func.count(Ticket.id)).where(Ticket.status == 'in_progress')) or 0,
                        await session.scalar(select(func.count(Ticket.id)).where(and_(Ticket.status == 'closed', Ticket.admin_answer.isnot(None)))) or 0,
                        await session.scalar(select(func.count(Ticket.id)).where(and_(Ticket.status == 'closed', Ticket.admin_answer.is_(None)))) or 0,
                        f"{(replied_tickets / total_tickets * 100):.1f}%" if total_tickets > 0 else "0%"
                    ]
                }
                df_summary = pd.DataFrame(summary_data)
                df_summary.to_excel(writer, sheet_name='Summary', index=False)
            
            output.seek(0)
            
            # Save and send
            filename = f'toonpay_detailed_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            with open(filename, 'wb') as f:
                f.write(output.getvalue())
            
            await message.reply_document(
                FSInputFile(filename),
                caption="✅ Complete detailed export with user-wise ticket history"
            )
            
            os.remove(filename)
            
        except Exception as e:
            logger.error(f"Export error: {e}")
            await message.reply(f"❌ Error generating export: {str(e)}")

@router.callback_query(F.data.startswith("export_"))
@admin_group_only()
async def export_callback(callback: CallbackQuery):
    """Handle export callbacks - WORKING VERSION"""
    export_type = callback.data.replace("export_", "")
    
    await callback.message.edit_text("📊 Generating export...")
    
    async for session in get_db():
        try:
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
            elif export_type == "month":
                since = datetime.utcnow() - timedelta(days=30)
                tickets_result = await session.execute(
                    select(Ticket).where(Ticket.created_at >= since)
                )
            else:
                tickets_result = await session.execute(select(Ticket))
            
            tickets = tickets_result.scalars().all()
            
            # Create export data
            export_data = []
            for ticket in tickets:
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
            
            os.remove(filename)
            await callback.message.delete()
            
        except Exception as e:
            logger.error(f"Export error: {e}")
            await callback.message.edit_text(f"❌ Error: {str(e)}")

# ==================== SUPER ADMIN PANEL ====================

@router.message(Command("panel"))
@super_admin_only()
async def super_admin_panel(message: Message):
    """Open super admin control panel"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Statistics", callback_data="sa_stats")],
        [InlineKeyboardButton(text="📋 All Tickets", callback_data="sa_tickets")],
        [InlineKeyboardButton(text="👥 Users", callback_data="sa_users")],
        [InlineKeyboardButton(text="📤 Export Data", callback_data="sa_export")],
        [InlineKeyboardButton(text="📢 Broadcast", callback_data="sa_broadcast")],
        [InlineKeyboardButton(text="⚙️ Groups", callback_data="sa_groups")],
        [InlineKeyboardButton(text="❌ Close", callback_data="sa_close")]
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
        await show_panel_stats(callback)
    elif action == "tickets":
        await show_panel_tickets(callback)
    elif action == "users":
        await show_panel_users(callback)
    elif action == "export":
        await show_panel_export(callback)
    elif action == "broadcast":
        await show_panel_broadcast(callback)
    elif action == "groups":
        await show_panel_groups(callback)
    elif action == "close":
        await callback.message.delete()
        await callback.answer("Panel closed")

async def show_panel_stats(callback: CallbackQuery):
    """Show statistics in panel"""
    async for session in get_db():
        users_count = await session.scalar(select(func.count(User.id))) or 0
        tickets_count = await session.scalar(select(func.count(Ticket.id))) or 0
        open_t = await session.scalar(select(func.count(Ticket.id)).where(Ticket.status == 'open')) or 0
        progress = await session.scalar(select(func.count(Ticket.id)).where(Ticket.status == 'in_progress')) or 0
        replied = await session.scalar(select(func.count(Ticket.id)).where(and_(Ticket.status == 'closed', Ticket.admin_answer.isnot(None)))) or 0
        closed_no = await session.scalar(select(func.count(Ticket.id)).where(and_(Ticket.status == 'closed', Ticket.admin_answer.is_(None)))) or 0
        
        text = f"""
<b>📊 Statistics</b>

<b>👥 Users:</b> {users_count}

<b>🎫 Tickets:</b> {tickets_count}
• 🟢 Open: {open_t}
• 🟡 In Progress: {progress}
• ✅ Replied: {replied}
• 🔴 Closed No Reply: {closed_no}

<b>📈 Response Rate:</b> {(replied/tickets_count*100):.1f}%""" if tickets_count > 0 else "No tickets"
        
        await callback.message.edit_text(text)
        await callback.answer()

async def show_panel_tickets(callback: CallbackQuery):
    """Show tickets overview in panel"""
    async for session in get_db():
        tickets = await session.execute(select(Ticket).order_by(Ticket.created_at.desc()).limit(10))
        tickets = tickets.scalars().all()
        
        if not tickets:
            await callback.message.edit_text("📭 No tickets found")
            await callback.answer()
            return
        
        text = "<b>📋 Recent Tickets:</b>\n\n"
        for t in tickets:
            status = '🟢' if t.status == 'open' else '🟡' if t.status == 'in_progress' else '🔴'
            text += f"{status} <code>{t.ticket_id}</code> - {t.category}\n"
            text += f"   From: {t.name}\n"
            text += f"   Created: {t.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        
        await callback.message.edit_text(text)
        await callback.answer()

async def show_panel_users(callback: CallbackQuery):
    """Show users overview in panel"""
    async for session in get_db():
        users = await session.execute(select(User).order_by(User.registered_at.desc()).limit(10))
        users = users.scalars().all()
        
        if not users:
            await callback.message.edit_text("👥 No users found")
            await callback.answer()
            return
        
        text = "<b>👥 Recent Users:</b>\n\n"
        for u in users:
            ticket_count = await session.scalar(select(func.count(Ticket.id)).where(Ticket.user_id == u.telegram_id)) or 0
            text += f"• @{u.username or 'N/A'} - {u.first_name}\n"
            text += f"  ID: <code>{u.telegram_id}</code>\n"
            text += f"  Tickets: {ticket_count}\n"
            text += f"  Registered: {u.registered_at.strftime('%Y-%m-%d')}\n\n"
        
        await callback.message.edit_text(text)
        await callback.answer()

async def show_panel_export(callback: CallbackQuery):
    """Show export options in panel"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Complete Export", callback_data="export_all")],
        [InlineKeyboardButton(text="🟢 Open Tickets", callback_data="export_open")],
        [InlineKeyboardButton(text="🟡 In Progress", callback_data="export_progress")],
        [InlineKeyboardButton(text="✅ Replied", callback_data="export_replied")],
        [InlineKeyboardButton(text="🔴 Closed No Reply", callback_data="export_closed_noreply")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="sa_stats")]
    ])
    
    await callback.message.edit_text(
        "📤 <b>Export Options</b>\n\n"
        "Select data to export:",
        reply_markup=keyboard
    )
    await callback.answer()

async def show_panel_broadcast(callback: CallbackQuery):
    """Show broadcast instructions"""
    await callback.message.edit_text(
        "📢 <b>Broadcast Message</b>\n\n"
        "Use: /broadcast Your message here\n\n"
        "Example: /broadcast Hello everyone!"
    )
    await callback.answer()

async def show_panel_groups(callback: CallbackQuery):
    """Show group management"""
    async for session in get_db():
        groups = await session.execute(select(AdminGroup).where(AdminGroup.is_active == True))
        groups = groups.scalars().all()
        
        text = "<b>⚙️ Active Groups:</b>\n\n"
        if groups:
            for g in groups:
                text += f"• <code>{g.group_id}</code>\n"
                text += f"  Added: {g.added_at.strftime('%Y-%m-%d')}\n\n"
        else:
            text += "No active groups\n\n"
        
        text += "Commands:\n/addgroup <id>\n/removegroup <id>"
        
        await callback.message.edit_text(text)
        await callback.answer()

# ==================== GROUP MANAGEMENT ====================

@router.message(Command("addgroup"))
@super_admin_only()
async def add_group(message: Message):
    """Add group to activated groups"""
    try:
        parts = message.text.split()
        if len(parts) != 2:
            await message.reply("❌ Usage: /addgroup <group_id>")
            return
            
        group_id = int(parts[1])
        
        async for session in get_db():
            result = await session.execute(
                select(AdminGroup).where(AdminGroup.group_id == group_id)
            )
            group = result.scalar_one_or_none()
            
            if group:
                group.is_active = True
            else:
                group = AdminGroup(
                    group_id=group_id,
                    group_name=f"Group_{group_id}",
                    added_by=message.from_user.id,
                    is_active=True
                )
                session.add(group)
            
            await session.commit()
            
        await message.reply(f"✅ Group {group_id} activated")
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")

@router.message(Command("removegroup"))
@super_admin_only()
async def remove_group(message: Message):
    """Remove group from activated groups"""
    try:
        parts = message.text.split()
        if len(parts) != 2:
            await message.reply("❌ Usage: /removegroup <group_id>")
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
                await message.reply(f"✅ Group {group_id} deactivated")
            else:
                await message.reply("❌ Group not found")
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")

@router.message(Command("listgroups"))
@super_admin_only()
async def list_groups(message: Message):
    """List all activated groups"""
    async for session in get_db():
        groups = await session.execute(select(AdminGroup).where(AdminGroup.is_active == True))
        groups = groups.scalars().all()
        
        if not groups:
            await message.reply("📭 No active groups")
            return
        
        response = "<b>📋 Active Groups:</b>\n\n"
        for group in groups:
            response += f"• <code>{group.group_id}</code>\n"
            response += f"  Added: {group.added_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        
        await message.reply(response)

# ==================== BROADCAST ====================

@router.message(Command("broadcast"))
@super_admin_only()
async def broadcast_message(message: Message):
    """Broadcast message to all users"""
    text = message.text.replace("/broadcast", "").strip()
    
    if not text:
        await message.reply("❌ Usage: /broadcast <message>")
        return
    
    await message.reply("📨 Broadcasting...")
    
    async for session in get_db():
        users = await session.execute(select(User))
        users = users.scalars().all()
        
        success = 0
        failed = 0
        
        for user in users:
            try:
                await message.bot.send_message(
                    user.telegram_id,
                    f"📢 <b>Announcement:</b>\n\n{text}\n\n⏱️ ToonPay Support 24/7"
                )
                success += 1
                await asyncio.sleep(0.05)
            except:
                failed += 1
        
        await message.reply(f"✅ Broadcast done!\n✓ Sent: {success}\n✗ Failed: {failed}")
