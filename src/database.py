# src/database.py
from sqlalchemy import create_engine, and_, or_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from datetime import datetime, timedelta
import random
import string
from typing import Optional, List, Dict, Any
import logging

from src.config import config
from src.models import Base, User, Ticket, Admin, AllowedGroup, AuditLog, Backup

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.engine = create_engine(
            config.DATABASE_URL,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=False
        )
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False)
        self.create_tables()
    
    def create_tables(self):
        """Create all tables"""
        Base.metadata.create_all(self.engine)
    
    @contextmanager
    def get_session(self):
        """Get database session"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            session.close()
    
    def generate_ticket_id(self) -> str:
        """Generate unique ticket ID"""
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"TKT-{timestamp}-{random_part}"
    
    # ========== USER METHODS ==========
    
    def get_or_create_user(self, user_id: int, username: str, full_name: str, 
                          email: str, phone: str) -> User:
        """Get or create user"""
        with self.get_session() as session:
            user = session.query(User).filter_by(user_id=user_id).first()
            
            if not user:
                user = User(
                    user_id=user_id,
                    username=username,
                    full_name=full_name,
                    email=email,
                    phone=phone
                )
                session.add(user)
                logger.info(f"New user created: {user_id}")
            else:
                user.last_active = datetime.utcnow()
                user.username = username
                if email:
                    user.email = email
                if phone:
                    user.phone = phone
            
            session.commit()
            return user
    
    def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        with self.get_session() as session:
            return session.query(User).filter_by(user_id=user_id).first()
    
    def search_users(self, query: str) -> List[User]:
        """Search users by various fields"""
        with self.get_session() as session:
            # Try to convert to int for user_id search
            try:
                user_id = int(query)
                return session.query(User).filter(
                    or_(
                        User.user_id == user_id,
                        User.username.ilike(f"%{query}%"),
                        User.full_name.ilike(f"%{query}%"),
                        User.email.ilike(f"%{query}%"),
                        User.phone.ilike(f"%{query}%")
                    )
                ).all()
            except ValueError:
                return session.query(User).filter(
                    or_(
                        User.username.ilike(f"%{query}%"),
                        User.full_name.ilike(f"%{query}%"),
                        User.email.ilike(f"%{query}%"),
                        User.phone.ilike(f"%{query}%")
                    )
                ).all()
    
    def get_all_users(self, limit: int = 1000) -> List[User]:
        """Get all users"""
        with self.get_session() as session:
            return session.query(User).order_by(User.registered_at.desc()).limit(limit).all()
    
    # ========== TICKET METHODS ==========
    
    def create_ticket(self, user_id: int, category: str, question: str) -> Ticket:
        """Create new ticket"""
        with self.get_session() as session:
            ticket_id = self.generate_ticket_id()
            
            ticket = Ticket(
                ticket_id=ticket_id,
                user_id=user_id,
                category=category,
                question=question,
                status='open'
            )
            session.add(ticket)
            
            # Update user ticket count
            user = session.query(User).filter_by(user_id=user_id).first()
            if user:
                user.total_tickets += 1
            
            session.commit()
            logger.info(f"New ticket created: {ticket_id} for user {user_id}")
            return ticket
    
    def get_ticket(self, ticket_id: str) -> Optional[Ticket]:
        """Get ticket by ID"""
        with self.get_session() as session:
            return session.query(Ticket).filter_by(ticket_id=ticket_id).first()
    
    def get_user_tickets(self, user_id: int, limit: int = 50) -> List[Ticket]:
        """Get all tickets for a user"""
        with self.get_session() as session:
            return session.query(Ticket)\
                .filter_by(user_id=user_id)\
                .order_by(Ticket.created_at.desc())\
                .limit(limit)\
                .all()
    
    def get_tickets_by_status(self, status: str = None, limit: int = 100) -> List[Ticket]:
        """Get tickets by status"""
        with self.get_session() as session:
            query = session.query(Ticket).order_by(Ticket.created_at.desc())
            if status:
                query = query.filter_by(status=status)
            return query.limit(limit).all()
    
    def get_all_tickets(self, limit: int = 1000) -> List[Ticket]:
        """Get all tickets"""
        with self.get_session() as session:
            return session.query(Ticket)\
                .order_by(Ticket.created_at.desc())\
                .limit(limit)\
                .all()
    
    def update_ticket_status(self, ticket_id: str, status: str, admin_id: int = None):
        """Update ticket status"""
        with self.get_session() as session:
            ticket = session.query(Ticket).filter_by(ticket_id=ticket_id).first()
            if ticket:
                ticket.status = status
                ticket.updated_at = datetime.utcnow()
                if admin_id:
                    ticket.assigned_to = admin_id
                if status in ['replied_closed', 'closed_no_reply']:
                    ticket.closed_at = datetime.utcnow()
                    ticket.closed_by = admin_id
                session.commit()
                logger.info(f"Ticket {ticket_id} status updated to {status}")
    
    def reply_to_ticket(self, ticket_id: str, reply: str, admin_id: int):
        """Reply to ticket and close it"""
        with self.get_session() as session:
            ticket = session.query(Ticket).filter_by(ticket_id=ticket_id).first()
            if ticket:
                ticket.admin_reply = reply
                ticket.status = 'replied_closed'
                ticket.updated_at = datetime.utcnow()
                ticket.closed_at = datetime.utcnow()
                ticket.closed_by = admin_id
                ticket.assigned_to = admin_id
                
                # Update admin stats
                admin = session.query(Admin).filter_by(user_id=admin_id).first()
                if admin:
                    admin.tickets_handled += 1
                
                session.commit()
                logger.info(f"Reply sent for ticket {ticket_id}")
    
    def close_ticket_no_reply(self, ticket_id: str, admin_id: int):
        """Close ticket without reply"""
        with self.get_session() as session:
            ticket = session.query(Ticket).filter_by(ticket_id=ticket_id).first()
            if ticket:
                ticket.status = 'closed_no_reply'
                ticket.updated_at = datetime.utcnow()
                ticket.closed_at = datetime.utcnow()
                ticket.closed_by = admin_id
                ticket.assigned_to = admin_id
                session.commit()
                logger.info(f"Ticket {ticket_id} closed without reply")
    
    # ========== ADMIN METHODS ==========
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        with self.get_session() as session:
            return session.query(Admin)\
                .filter_by(user_id=user_id, is_active=True)\
                .first() is not None
    
    def is_super_admin(self, user_id: int) -> bool:
        """Check if user is super admin"""
        with self.get_session() as session:
            admin = session.query(Admin)\
                .filter_by(user_id=user_id, is_active=True)\
                .first()
            return admin and admin.is_super_admin
    
    def add_admin(self, user_id: int, username: str, added_by: int, is_super: bool = False):
        """Add new admin"""
        with self.get_session() as session:
            admin = Admin(
                user_id=user_id,
                username=username,
                added_by=added_by,
                is_super_admin=is_super
            )
            session.add(admin)
            session.commit()
            logger.info(f"New admin added: {user_id} (super: {is_super})")
    
    def remove_admin(self, user_id: int):
        """Remove admin"""
        with self.get_session() as session:
            admin = session.query(Admin).filter_by(user_id=user_id).first()
            if admin and not admin.is_super_admin:
                admin.is_active = False
                session.commit()
                logger.info(f"Admin removed: {user_id}")
    
    def get_all_admins(self) -> List[Admin]:
        """Get all active admins"""
        with self.get_session() as session:
            return session.query(Admin).filter_by(is_active=True).all()
    
    # ========== GROUP METHODS ==========
    
    def add_allowed_group(self, group_id: int, group_title: str, added_by: int):
        """Add group to allowed list"""
        with self.get_session() as session:
            group = AllowedGroup(
                group_id=group_id,
                group_title=group_title,
                added_by=added_by
            )
            session.add(group)
            session.commit()
            logger.info(f"Group added: {group_id}")
    
    def remove_allowed_group(self, group_id: int):
        """Remove group from allowed list"""
        with self.get_session() as session:
            group = session.query(AllowedGroup).filter_by(group_id=group_id).first()
            if group:
                group.is_active = False
                session.commit()
                logger.info(f"Group removed: {group_id}")
    
    def is_group_allowed(self, group_id: int) -> bool:
        """Check if group is allowed to use bot"""
        with self.get_session() as session:
            return session.query(AllowedGroup)\
                .filter_by(group_id=group_id, is_active=True)\
                .first() is not None
    
    def get_allowed_groups(self) -> List[AllowedGroup]:
        """Get all allowed groups"""
        with self.get_session() as session:
            return session.query(AllowedGroup).filter_by(is_active=True).all()
    
    # ========== STATISTICS ==========
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics"""
        with self.get_session() as session:
            stats = {
                'total_users': session.query(User).count(),
                'total_tickets': session.query(Ticket).count(),
                'open': session.query(Ticket).filter_by(status='open').count(),
                'in_progress': session.query(Ticket).filter_by(status='in_progress').count(),
                'replied_closed': session.query(Ticket).filter_by(status='replied_closed').count(),
                'closed_no_reply': session.query(Ticket).filter_by(status='closed_no_reply').count(),
                'total_admins': session.query(Admin).filter_by(is_active=True).count(),
                'total_groups': session.query(AllowedGroup).filter_by(is_active=True).count()
            }
            
            # Category breakdown
            categories = {}
            for cat in ['card', 'kyc', 'technical', 'payment', 'other']:
                categories[cat] = session.query(Ticket).filter_by(category=cat).count()
            stats['categories'] = categories
            
            # Today's tickets
            today = datetime.utcnow().date()
            stats['today_tickets'] = session.query(Ticket)\
                .filter(Ticket.created_at >= today)\
                .count()
            
            return stats
    
    def get_user_statistics(self, user_id: int) -> Dict[str, int]:
        """Get statistics for a specific user"""
        with self.get_session() as session:
            stats = {
                'total': session.query(Ticket).filter_by(user_id=user_id).count(),
                'open': session.query(Ticket).filter_by(user_id=user_id, status='open').count(),
                'in_progress': session.query(Ticket).filter_by(user_id=user_id, status='in_progress').count(),
                'replied_closed': session.query(Ticket).filter_by(user_id=user_id, status='replied_closed').count(),
                'closed_no_reply': session.query(Ticket).filter_by(user_id=user_id, status='closed_no_reply').count()
            }
            return stats
    
    # ========== AUDIT LOG ==========
    
    def log_action(self, admin_id: int, action: str, details: dict = None):
        """Log admin action"""
        with self.get_session() as session:
            log = AuditLog(
                admin_id=admin_id,
                action=action,
                details=details or {}
            )
            session.add(log)
            session.commit()
    
    # ========== BACKUP METHODS ==========
    
    def save_backup_record(self, filename: str, size: int, message_id: int = None):
        """Save backup record"""
        with self.get_session() as session:
            backup = Backup(
                filename=filename,
                size=size,
                message_id=message_id
            )
            session.add(backup)
            session.commit()
            return backup
    
    def get_backups(self, limit: int = 10) -> List[Backup]:
        """Get recent backups"""
        with self.get_session() as session:
            return session.query(Backup)\
                .order_by(Backup.created_at.desc())\
                .limit(limit)\
                .all()

# Create global database instance
db = Database()
