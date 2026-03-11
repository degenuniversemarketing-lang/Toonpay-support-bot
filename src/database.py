from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Text, BigInteger, Boolean, select
from datetime import datetime
from config import Config
import asyncpg
import logging

# Configure logger
logger = logging.getLogger(__name__)

# Convert postgresql:// to postgresql+asyncpg://
if Config.DATABASE_URL:
    DATABASE_URL = Config.DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')
else:
    raise ValueError("DATABASE_URL not set in environment variables")

# Create engine with connection pooling
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True
)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

# Models
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    phone = Column(String(50))
    email = Column(String(255))
    registered_at = Column(DateTime, default=datetime.utcnow)
    is_blocked = Column(Boolean, default=False)
    
class Ticket(Base):
    __tablename__ = 'tickets'
    
    id = Column(Integer, primary_key=True)
    ticket_id = Column(String(50), unique=True, nullable=False)
    user_id = Column(BigInteger, nullable=False)
    user_name = Column(String(255))
    category = Column(String(100))
    name = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    description = Column(Text)
    status = Column(String(50), default='open')
    created_at = Column(DateTime, default=datetime.utcnow)
    admin_answer = Column(Text)
    answered_by = Column(BigInteger)
    answered_at = Column(DateTime)
    in_progress_by = Column(BigInteger)
    in_progress_at = Column(DateTime)
    admin_group_message_id = Column(Integer)
    
class AdminGroup(Base):
    __tablename__ = 'admin_groups'
    
    id = Column(Integer, primary_key=True)
    group_id = Column(BigInteger, unique=True, nullable=False)
    group_name = Column(String(255))
    added_by = Column(BigInteger)
    added_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
class BotCommand(Base):
    __tablename__ = 'bot_commands'
    
    id = Column(Integer, primary_key=True)
    command = Column(String(100), unique=True)
    response_text = Column(Text)
    is_active = Column(Boolean, default=True)
    updated_by = Column(BigInteger)
    updated_at = Column(DateTime, default=datetime.utcnow)

async def get_db():
    """Get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified")
