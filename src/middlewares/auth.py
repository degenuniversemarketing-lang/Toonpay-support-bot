from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable
from sqlalchemy import select
from database import get_db
from models import AdminGroup

class GroupAuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # Skip for private chats
        if event.chat.type == 'private':
            return await handler(event, data)
        
        # Check if group is activated for support
        if event.chat.type in ['group', 'supergroup']:
            async for session in get_db():
                result = await session.execute(
                    select(AdminGroup).where(
                        AdminGroup.group_id == event.chat.id,
                        AdminGroup.is_active == True
                    )
                )
                group = result.scalar_one_or_none()
                
                if not group and event.text and event.text.startswith('/support'):
                    await event.reply("❌ Support bot is not activated in this group.")
                    return
                
                # Store group info in data
                data['is_activated_group'] = group is not None
        
        return await handler(event, data)
