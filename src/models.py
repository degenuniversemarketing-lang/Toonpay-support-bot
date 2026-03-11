# src/models.py
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, BigInteger, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import json

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255))
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=False)
    registered_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    total_tickets = Column(Integer, default=0)
    is_blocked = Column(Boolean, default=False)
    metadata = Column(JSON, default={})
    
    tickets = relationship("Ticket", back_populates="user", cascade="all, delete-orphan")

class Ticket(Base):
    __tablename__ = 'tickets'
    
    id = Column(Integer, primary_key=True)
    ticket_id = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    category = Column(String(50), nullable=False)
    question = Column(Text, nullable=False)
    admin_reply = Column(Text)
    status = Column(String(20), default='open', index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    assigned_to = Column(BigInteger)
    closed_by = Column(BigInteger)
    closed_at = Column(DateTime)
    admin_notes = Column(Text)
    attachments = Column(JSON, default=[])
    
    user = relationship("User", back_populates="tickets")

class Admin(Base):
    __tablename__ = 'admins'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255))
    added_by = Column(BigInteger)
    added_at = Column(DateTime, default=datetime.utcnow)
    is_super_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    permissions = Column(JSON, default={})
    tickets_handled = Column(Integer, default=0)

class AllowedGroup(Base):
    __tablename__ = 'allowed_groups'
    
    id = Column(Integer, primary_key=True)
    group_id = Column(BigInteger, unique=True, nullable=False, index=True)
    group_title = Column(String(255))
    added_by = Column(BigInteger)
    added_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True)
    admin_id = Column(BigInteger, nullable=False)
    action = Column(String(255), nullable=False)
    details = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Backup(Base):
    __tablename__ = 'backups'
    
    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    size = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default='completed')
    message_id = Column(BigInteger)  # Telegram message ID of backup
