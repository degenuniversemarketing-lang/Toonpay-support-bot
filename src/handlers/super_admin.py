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
                    'Replied & Closed': sum(1 for t in tickets if t.status == 'closed' and t.admin_answer),
                    'Closed No Reply': sum(1 for t in tickets if t.status == 'closed' and not t.admin_answer)
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
                        'Email': user.email or 'Not provided',
                        'Phone': user.phone or 'Not provided',
                        'Ticket ID': ticket.ticket_id,
                        'Category': ticket.category,
                        'Status': ticket_status,
                        'Created': ticket.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'User Question': ticket.description,
                        'Admin Answer': ticket.admin_answer or 'No reply yet',
                        'Answered By': f"@{ticket.answered_by}" if ticket.answered_by else 'N/A',
                        'Answered At': ticket.answered_at.strftime('%Y-%m-%d %H:%M:%S') if ticket.answered_at else 'N/A',
                        'In Progress By': f"@{ticket.in_progress_by}" if ticket.in_progress_by else 'N/A'
                    })
            
            # Create DataFrames
            df_detailed = pd.DataFrame(users_data)
            
            # Write to Excel
            df_detailed.to_excel(writer, sheet_name='Detailed Report', index=False)
            
            # Summary Sheet
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
                    sum(len(u_data) for u_data in [await session.execute(select(Ticket).where(Ticket.user_id == u.telegram_id)) for u in users]),
                    await session.scalar(select(func.count(Ticket.id)).where(Ticket.status == 'open')),
                    await session.scalar(select(func.count(Ticket.id)).where(Ticket.status == 'in_progress')),
                    await session.scalar(select(func.count(Ticket.id)).where(and_(Ticket.status == 'closed', Ticket.admin_answer.isnot(None)))),
                    await session.scalar(select(func.count(Ticket.id)).where(and_(Ticket.status == 'closed', Ticket.admin_answer.is_(None)))),
                    f"{(await session.scalar(select(func.count(Ticket.id)).where(Ticket.admin_answer.isnot(None))) / await session.scalar(select(func.count(Ticket.id))) * 100):.1f}%" if await session.scalar(select(func.count(Ticket.id))) > 0 else "0%"
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

# ==================== ENHANCED TICKETS COMMAND ====================

@router.message(Command("tickets"))
@admin_group_only()
async def enhanced_tickets_list(message: Message):
    """Enhanced tickets list with links and detailed status"""
    async for session in get_db():
        # Get all tickets
        result = await session.execute(
            select(Ticket).order_by(Ticket.created_at.desc())
        )
        tickets = result.scalars().all()
        
        if not tickets:
            await message.reply("📭 No tickets found")
            return
        
        # Group tickets by user
        user_tickets = {}
        for ticket in tickets:
            if ticket.user_id not in user_tickets:
                user_tickets[ticket.user_id] = []
            user_tickets[ticket.user_id].append(ticket)
        
        response = "<b>📋 All Tickets Overview</b>\n\n"
        
        for user_id, user_ticket_list in user_tickets.items():
            # Get user info
            user_result = await session.execute(
                select(User).where(User.telegram_id == user_id)
            )
            user = user_result.scalar_one_or_none()
            
            if user:
                response += f"<b>👤 User: {user.first_name} (@{user.username if user.username else 'N/A'})</b>\n"
                
                for ticket in user_ticket_list[:3]:  # Show last 3 tickets per user
                    status_emoji = '🟢' if ticket.status == 'open' else '🟡' if ticket.status == 'in_progress' else '🔴'
                    status_text = 'Open' if ticket.status == 'open' else 'In Progress' if ticket.status == 'in_progress' else 'Closed'
                    
                    # Generate message link
                    if ticket.admin_group_message_id:
                        message_link = f"https://t.me/c/{str(Config.ADMIN_GROUP_ID).replace('-100', '')}/{ticket.admin_group_message_id}"
                        ticket_link = f"<a href='{message_link}'>📎 View Ticket</a>"
                    else:
                        ticket_link = "No link"
                    
                    response += f"\n{status_emoji} <code>{ticket.ticket_id}</code> - {ticket.category}\n"
                    response += f"   From: {ticket.name}\n"
                    response += f"   Created: {ticket.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                    
                    if ticket.status == 'in_progress' and ticket.in_progress_by:
                        # Get admin username
                        response += f"   🟡 In Progress by: <code>Admin {ticket.in_progress_by}</code>\n"
                        response += f"   {ticket_link} | <b>Question:</b> {ticket.description[:50]}...\n"
                    
                    elif ticket.status == 'closed':
                        if ticket.admin_answer:
                            response += f"   ✅ Replied by: <code>Admin {ticket.answered_by}</code>\n"
                            response += f"   <b>Reply:</b> {ticket.admin_answer[:50]}...\n"
                        else:
                            response += f"   🔴 Closed by: <code>Admin {ticket.answered_by}</code> (No reply)\n"
                    
                    else:  # Open
                        response += f"   🟢 Waiting for admin\n"
                        response += f"   <b>Question:</b> {ticket.description[:50]}...\n"
                    
                    response += f"   {ticket_link}\n\n"
                
                if len(user_ticket_list) > 3:
                    response += f"   <i>... and {len(user_ticket_list) - 3} more tickets</i>\n\n"
                
                response += "─" * 30 + "\n\n"
        
        # Split long messages
        if len(response) > 4000:
            parts = [response[i:i+4000] for i in range(0, len(response), 4000)]
            for part in parts:
                await message.reply(part)
        else:
            await message.reply(response)

# ==================== ENHANCED SEARCH COMMAND ====================

@router.message(Command("search"))
@admin_group_only()
async def enhanced_search_user(message: Message):
    """Enhanced search with user details and ticket management"""
    search_term = message.text.replace("/search", "").strip()
    
    if not search_term:
        await message.reply("Usage: /search <username/email/user_id/phone>")
        return
    
    async for session in get_db():
        # Search users
        query = select(User).where(
            or_(
                User.username.ilike(f"%{search_term}%"),
                User.email.ilike(f"%{search_term}%"),
                User.telegram_id == (int(search_term) if search_term.isdigit() else 0),
                User.phone.ilike(f"%{search_term}%"),
                User.first_name.ilike(f"%{search_term}%"),
                User.last_name.ilike(f"%{search_term}%")
            )
        )
        result = await session.execute(query)
        users = result.scalars().all()
        
        if not users:
            await message.reply("❌ No users found")
            return
        
        for user in users:
            # Get user's tickets
            tickets_query = select(Ticket).where(Ticket.user_id == user.telegram_id).order_by(Ticket.created_at.desc())
            tickets_result = await session.execute(tickets_query)
            tickets = tickets_result.scalars().all()
            
            # Calculate statistics
            total_tickets = len(tickets)
            open_tickets = sum(1 for t in tickets if t.status == 'open')
            in_progress = sum(1 for t in tickets if t.status == 'in_progress')
            replied_closed = sum(1 for t in tickets if t.status == 'closed' and t.admin_answer)
            closed_no_reply = sum(1 for t in tickets if t.status == 'closed' and not t.admin_answer)
            
            # Format response with user details
            response = f"""
<b>👤 User Found:</b>
• ID: <code>{user.telegram_id}</code>
• Username: @{user.username if user.username else 'N/A'}
• Name: {user.first_name} {user.last_name or ''}
• Email: {user.email or 'Not provided'}
• Phone: {user.phone or 'Not provided'}
• Registered: {user.registered_at.strftime('%Y-%m-%d %H:%M')}

<b>📊 Statistics:</b>
• Total Tickets: {total_tickets}
• 🟢 Open: {open_tickets}
• 🟡 In Progress: {in_progress}
• ✅ Replied & Closed: {replied_closed}
• 🔴 Closed without reply: {closed_no_reply}

<b>📋 Recent Tickets:</b>
"""
            for ticket in tickets[:5]:  # Show last 5 tickets
                status_emoji = '🟢' if ticket.status == 'open' else '🟡' if ticket.status == 'in_progress' else '🔴'
                
                # Generate message link
                if ticket.admin_group_message_id:
                    message_link = f"https://t.me/c/{str(Config.ADMIN_GROUP_ID).replace('-100', '')}/{ticket.admin_group_message_id}"
                    view_link = f"<a href='{message_link}'>📎 View</a>"
                else:
                    view_link = "No link"
                
                response += f"\n{status_emoji} <code>{ticket.ticket_id}</code> - {ticket.category}\n"
                response += f"   Created: {ticket.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                response += f"   <b>Question:</b> {ticket.description[:100]}...\n"
                
                if ticket.status == 'in_progress':
                    response += f"   🟡 In Progress by: Admin {ticket.in_progress_by}\n"
                    response += f"   {view_link} | <a href='https://t.me/{message.bot.username}?start=reply_{ticket.ticket_id}'>💬 Reply</a>\n"
                elif ticket.status == 'closed':
                    if ticket.admin_answer:
                        response += f"   ✅ <b>Reply:</b> {ticket.admin_answer[:100]}...\n"
                        response += f"   Replied by: Admin {ticket.answered_by}\n"
                    else:
                        response += f"   🔴 Closed without reply by: Admin {ticket.answered_by}\n"
                else:  # Open
                    response += f"   🟢 <a href='https://t.me/{message.bot.username}?start=reply_{ticket.ticket_id}'>💬 Click to reply</a>\n"
            
            await message.reply(response)

# ==================== REPLY BY COMMAND ====================

@router.message(Command("reply"))
@admin_group_only()
async def reply_by_command(message: Message):
    """Reply to ticket using command: /reply TICKET_ID Your message"""
    try:
        # Parse command: /reply TICKET_ID Your message here
        text = message.text.replace("/reply", "").strip()
        parts = text.split(maxsplit=1)
        
        if len(parts) != 2:
            await message.reply("❌ Usage: /reply TICKET_ID Your reply message")
            return
        
        ticket_id, reply_text = parts
        
        async for session in get_db():
            # Find ticket
            result = await session.execute(
                select(Ticket).where(Ticket.ticket_id == ticket_id)
            )
            ticket = result.scalar_one_or_none()
            
            if not ticket:
                await message.reply(f"❌ Ticket {ticket_id} not found")
                return
            
            # Update ticket
            ticket.admin_answer = reply_text
            ticket.answered_by = message.from_user.id
            ticket.answered_at = datetime.utcnow()
            ticket.status = 'closed'
            
            await session.commit()
            
            # Send reply to user
            await message.bot.send_message(
                ticket.user_id,
                f"📬 <b>Reply to your ticket #{ticket_id}</b>\n\n"
                f"<b>Support Team:</b>\n{reply_text}\n\n"
                f"<i>This ticket is now closed. ToonPay Support available 24/7.</i>"
            )
            
            # Update admin group message if exists
            if ticket.admin_group_message_id:
                try:
                    await message.bot.edit_message_text(
                        chat_id=Config.ADMIN_GROUP_ID,
                        message_id=ticket.admin_group_message_id,
                        text=f"✅ <b>Ticket {ticket_id} - Closed</b>\n\n"
                             f"<b>Reply sent by:</b> @{message.from_user.username}\n"
                             f"<b>Reply:</b> {reply_text}",
                        reply_markup=None
                    )
                except:
                    pass
            
            await message.reply(f"✅ Reply sent for ticket {ticket_id}")
            
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")

# ==================== STATISTICS WITH FILTERS ====================

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
        base_query = select(func.count(Ticket.id))
        
        if filter_type == "general":
            # General stats
            total = await session.scalar(select(func.count(Ticket.id)))
            open_t = await session.scalar(select(func.count(Ticket.id)).where(Ticket.status == 'open'))
            progress = await session.scalar(select(func.count(Ticket.id)).where(Ticket.status == 'in_progress'))
            replied = await session.scalar(select(func.count(Ticket.id)).where(and_(Ticket.status == 'closed', Ticket.admin_answer.isnot(None))))
            closed_no = await session.scalar(select(func.count(Ticket.id)).where(and_(Ticket.status == 'closed', Ticket.admin_answer.is_(None))))
            
            stats_text = f"""
<b>📊 General Statistics</b>

<b>🎫 Tickets Overview:</b>
• Total Tickets: {total or 0}
• 🟢 Open: {open_t or 0}
• 🟡 In Progress: {progress or 0}
• ✅ Replied & Closed: {replied or 0}
• 🔴 Closed No Reply: {closed_no or 0}

<b>📈 Performance:</b>
• Response Rate: {((replied or 0) / (total or 1) * 100):.1f}%
• Total Users: {await session.scalar(select(func.count(User.id))) or 0}
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
        
        await callback.message.edit_text(stats_text)
        await callback.answer()
