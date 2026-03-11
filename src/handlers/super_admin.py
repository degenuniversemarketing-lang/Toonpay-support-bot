from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
from sqlalchemy import select, func
from database import get_db
from database import AdminGroup, BotCommand, User, Ticket
from utils.decorators import super_admin_only
from utils.helpers import format_user_data_for_export
from config import Config
from datetime import datetime, timedelta
import os
import io

router = Router()

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

@router.message(Command("getdata"))
@super_admin_only()
async def get_all_data(message: Message):
    """Export all data as Excel file"""
    await message.reply("📊 Generating data export...")
    
    async for session in get_db():
        # Get all users
        users_result = await session.execute(select(User))
        users = users_result.scalars().all()
        
        # Get all tickets
        tickets_result = await session.execute(select(Ticket))
        tickets = tickets_result.scalars().all()
        
        # Prepare data for export
        users_data = []
        for user in users:
            users_data.append({
                'Telegram ID': user.telegram_id,
                'Username': user.username,
                'First Name': user.first_name,
                'Last Name': user.last_name,
                'Email': user.email,
                'Phone': user.phone,
                'Registered At': user.registered_at.strftime('%Y-%m-%d %H:%M:%S'),
                'Is Blocked': user.is_blocked
            })
        
        tickets_data = []
        for ticket in tickets:
            tickets_data.append({
                'Ticket ID': ticket.ticket_id,
                'User ID': ticket.user_id,
                'User Name': ticket.user_name,
                'Category': ticket.category,
                'Name': ticket.name,
                'Email': ticket.email,
                'Phone': ticket.phone,
                'Description': ticket.description,
                'Status': ticket.status,
                'Created At': ticket.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'Admin Answer': ticket.admin_answer,
                'Answered By': ticket.answered_by,
                'Answered At': ticket.answered_at.strftime('%Y-%m-%d %H:%M:%S') if ticket.answered_at else None,
                'In Progress By': ticket.in_progress_by
            })
        
        # Create Excel file
        excel_file = format_user_data_for_export(users_data, tickets_data)
        
        # Save temporarily
        filename = f'toonpay_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        with open(filename, 'wb') as f:
            f.write(excel_file.getvalue())
        
        # Send file
        await message.reply_document(
            FSInputFile(filename),
            caption="✅ Complete data export"
        )
        
        # Clean up
        os.remove(filename)

@router.message(Command("stats"))
@super_admin_only()
async def show_statistics(message: Message):
    """Show bot statistics"""
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
        closed_tickets = await session.scalar(
            select(func.count(Ticket.id)).where(Ticket.status == 'closed')
        )
        
        # Get today's tickets
        today = datetime.utcnow().date()
        today_tickets = await session.scalar(
            select(func.count(Ticket.id)).where(
                func.date(Ticket.created_at) == today
            )
        )
        
        # Get this week's tickets
        week_ago = datetime.utcnow() - timedelta(days=7)
        week_tickets = await session.scalar(
            select(func.count(Ticket.id)).where(Ticket.created_at >= week_ago)
        )
        
        # Get active groups
        active_groups = await session.scalar(
            select(func.count(AdminGroup.id)).where(AdminGroup.is_active == True)
        )
        
        # Get response rate
        answered_tickets = await session.scalar(
            select(func.count(Ticket.id)).where(Ticket.admin_answer.isnot(None))
        )
        response_rate = (answered_tickets / tickets_count * 100) if tickets_count else 0
        
        stats_message = f"""
<b>📊 Bot Statistics</b>

<b>👥 Users:</b>
• Total Users: {users_count or 0}

<b>🎫 Tickets:</b>
• Total Tickets: {tickets_count or 0}
• 🟢 Open: {open_tickets or 0}
• 🟡 In Progress: {progress_tickets or 0}
• 🔴 Closed: {closed_tickets or 0}
• 📅 Today: {today_tickets or 0}
• 📆 This Week: {week_tickets or 0}

<b>📈 Performance:</b>
• Response Rate: {response_rate:.1f}%
• Answered: {answered_tickets or 0}

<b>⚙️ Settings:</b>
• Active Groups: {active_groups or 0}
• Admin Group: {Config.ADMIN_GROUP_ID}
"""
        await message.reply(stats_message)

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
        await message.reply(f"❌ Error: {str(e)}")

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
                    f"📢 <b>Announcement:</b>\n\n{text}"
                )
                success += 1
            except Exception:
                failed += 1
            
            # Small delay to avoid flooding
            await asyncio.sleep(0.05)
        
        await message.reply(f"✅ Broadcast completed!\n✓ Sent: {success}\n✗ Failed: {failed}")
