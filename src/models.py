from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from src.database import Base

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    tickets = relationship('Ticket', back_populates='user', cascade='all, delete-orphan')

class Ticket(Base):
    __tablename__ = 'tickets'
    
    id = Column(Integer, primary_key=True)
    ticket_number = Column(String(50), unique=True, nullable=False)
    user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    category = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=False)
    question = Column(Text, nullable=False)
    status = Column(String(50), default='new')
    admin_reply = Column(Text, nullable=True)
    admin_username = Column(String(255), nullable=True)
    replied_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship('User', back_populates='tickets')

class Group(Base):
    __tablename__ = 'groups'
    
    id = Column(Integer, primary_key=True)
    group_id = Column(BigInteger, unique=True, nullable=False)
    group_title = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    added_by = Column(BigInteger, nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)

class AdminAction(Base):
    __tablename__ = 'admin_actions'
    
    id = Column(Integer, primary_key=True)
    admin_id = Column(BigInteger, nullable=False)
    admin_username = Column(String(255), nullable=True)
    action = Column(String(50), nullable=False)
    ticket_number = Column(String(50), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
