import os
import psycopg2
from psycopg2.extras import RealDictCursor
import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.conn = psycopg2.connect(os.environ['DATABASE_URL'])
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Create tables one by one with proper error handling
        
        # Users table
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username VARCHAR(255),
                    first_name VARCHAR(255),
                    last_name VARCHAR(255),
                    email VARCHAR(255),
                    phone VARCHAR(20),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            logger.info("Users table created/verified")
        except Exception as e:
            logger.error(f"Error creating users table: {e}")
        
        # Admin groups table (legacy - for backward compatibility)
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_groups (
                    group_id BIGINT PRIMARY KEY,
                    added_by BIGINT,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            logger.info("Admin groups table created/verified")
        except Exception as e:
            logger.error(f"Error creating admin_groups table: {e}")
        
        # Activated groups table (for /support command)
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS activated_groups (
                    group_id BIGINT PRIMARY KEY,
                    activated_by BIGINT,
                    activated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            logger.info("Activated groups table created/verified")
        except Exception as e:
            logger.error(f"Error creating activated_groups table: {e}")
        
        # Tickets table - without foreign key first
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tickets (
                    ticket_id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    question TEXT,
                    admin_answer TEXT,
                    status VARCHAR(50) DEFAULT 'pending',
                    replied_by BIGINT,
                    replied_by_username VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP
                )
            ''')
            logger.info("Tickets table created/verified")
        except Exception as e:
            logger.error(f"Error creating tickets table: {e}")
        
        # Ticket logs table - without foreign key first
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ticket_logs (
                    log_id SERIAL PRIMARY KEY,
                    ticket_id INTEGER,
                    action VARCHAR(50),
                    admin_id BIGINT,
                    admin_username VARCHAR(255),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            logger.info("Ticket logs table created/verified")
        except Exception as e:
            logger.error(f"Error creating ticket_logs table: {e}")
        
        self.conn.commit()
        
        # Now add indexes for better performance
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tickets_user_id ON tickets(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tickets_created_at ON tickets(created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ticket_logs_ticket_id ON ticket_logs(ticket_id)')
            logger.info("Indexes created/verified")
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
        
        self.conn.commit()
        cursor.close()
        logger.info("Database initialization complete")
    
    # User methods
    def add_user(self, user_id, username, first_name, last_name=None):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO users (user_id, username, first_name, last_name)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id) 
                DO UPDATE SET username = EXCLUDED.username,
                             first_name = EXCLUDED.first_name,
                             last_name = EXCLUDED.last_name
            ''', (user_id, username, first_name, last_name))
            self.conn.commit()
            cursor.close()
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            self.conn.rollback()
    
    def update_user_contact(self, user_id, email, phone):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET email = %s, phone = %s
                WHERE user_id = %s
            ''', (email, phone, user_id))
            self.conn.commit()
            cursor.close()
        except Exception as e:
            logger.error(f"Error updating user contact: {e}")
            self.conn.rollback()
    
    def get_user(self, user_id):
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
            user = cursor.fetchone()
            cursor.close()
            return user
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    # Ticket methods
    def create_ticket(self, user_id, question):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO tickets (user_id, question, status)
                VALUES (%s, %s, 'pending')
                RETURNING ticket_id
            ''', (user_id, question))
            ticket_id = cursor.fetchone()[0]
            self.conn.commit()
            cursor.close()
            return ticket_id
        except Exception as e:
            logger.error(f"Error creating ticket: {e}")
            self.conn.rollback()
            return None
    
    def get_pending_tickets(self):
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('''
                SELECT t.*, u.username, u.first_name, u.last_name, u.email, u.phone
                FROM tickets t
                LEFT JOIN users u ON t.user_id = u.user_id
                WHERE t.status IN ('pending', 'in_progress')
                ORDER BY t.created_at DESC
            ''')
            tickets = cursor.fetchall()
            cursor.close()
            return tickets
        except Exception as e:
            logger.error(f"Error getting pending tickets: {e}")
            return []
    
    def get_user_tickets(self, user_id):
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('''
                SELECT * FROM tickets 
                WHERE user_id = %s 
                ORDER BY created_at DESC
            ''', (user_id,))
            tickets = cursor.fetchall()
            cursor.close()
            return tickets
        except Exception as e:
            logger.error(f"Error getting user tickets: {e}")
            return []
    
    def get_ticket(self, ticket_id):
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('''
                SELECT t.*, u.username, u.first_name, u.last_name, u.email, u.phone
                FROM tickets t
                LEFT JOIN users u ON t.user_id = u.user_id
                WHERE t.ticket_id = %s
            ''', (ticket_id,))
            ticket = cursor.fetchone()
            cursor.close()
            return ticket
        except Exception as e:
            logger.error(f"Error getting ticket: {e}")
            return None
    
    def reply_to_ticket(self, ticket_id, admin_answer, admin_id, admin_username):
        try:
            cursor = self.conn.cursor()
            
            # First check if ticket exists and is not closed
            cursor.execute('SELECT status FROM tickets WHERE ticket_id = %s', (ticket_id,))
            result = cursor.fetchone()
            
            if not result:
                logger.warning(f"Ticket {ticket_id} not found")
                return False
            
            if result[0] == 'closed':
                logger.warning(f"Ticket {ticket_id} is already closed")
                return False
            
            # Update ticket
            cursor.execute('''
                UPDATE tickets 
                SET admin_answer = %s, 
                    replied_by = %s, 
                    replied_by_username = %s,
                    status = 'closed',
                    closed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE ticket_id = %s
                RETURNING ticket_id
            ''', (admin_answer, admin_id, admin_username, ticket_id))
            
            result = cursor.fetchone()
            
            if result:
                # Log the action
                cursor.execute('''
                    INSERT INTO ticket_logs (ticket_id, action, admin_id, admin_username)
                    VALUES (%s, 'replied', %s, %s)
                ''', (ticket_id, admin_id, admin_username))
            
            self.conn.commit()
            cursor.close()
            return result is not None
            
        except Exception as e:
            logger.error(f"Error replying to ticket: {e}")
            self.conn.rollback()
            return False
    
    def update_ticket_status(self, ticket_id, status, admin_id, admin_username):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE tickets 
                SET status = %s, 
                    replied_by = %s, 
                    replied_by_username = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE ticket_id = %s
            ''', (status, admin_id, admin_username, ticket_id))
            
            # Log the action
            cursor.execute('''
                INSERT INTO ticket_logs (ticket_id, action, admin_id, admin_username)
                VALUES (%s, %s, %s, %s)
            ''', (ticket_id, status, admin_id, admin_username))
            
            self.conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error updating ticket status: {e}")
            self.conn.rollback()
            return False
    
    # Admin group methods (legacy)
    def add_admin_group(self, group_id, added_by):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO admin_groups (group_id, added_by)
                VALUES (%s, %s)
                ON CONFLICT (group_id) DO NOTHING
            ''', (group_id, added_by))
            self.conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error adding admin group: {e}")
            self.conn.rollback()
            return False
    
    def remove_admin_group(self, group_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM admin_groups WHERE group_id = %s', (group_id,))
            self.conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error removing admin group: {e}")
            self.conn.rollback()
            return False
    
    def get_admin_groups(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT group_id FROM admin_groups')
            groups = [row[0] for row in cursor.fetchall()]
            cursor.close()
            return groups
        except Exception as e:
            logger.error(f"Error getting admin groups: {e}")
            return []
    
    # Activated groups methods (for /support command)
    def activate_group(self, group_id, activated_by):
        """Activate a group for /support command"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO activated_groups (group_id, activated_by)
                VALUES (%s, %s)
                ON CONFLICT (group_id) DO NOTHING
            ''', (group_id, activated_by))
            self.conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error activating group: {e}")
            self.conn.rollback()
            return False

    def deactivate_group(self, group_id):
        """Deactivate a group"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM activated_groups WHERE group_id = %s', (group_id,))
            self.conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error deactivating group: {e}")
            self.conn.rollback()
            return False

    def get_activated_groups(self):
        """Get all activated groups"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT group_id FROM activated_groups')
            groups = [row[0] for row in cursor.fetchall()]
            cursor.close()
            return groups
        except Exception as e:
            logger.error(f"Error getting activated groups: {e}")
            return []

    def is_group_activated(self, group_id):
        """Check if a group is activated"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT 1 FROM activated_groups WHERE group_id = %s', (group_id,))
            result = cursor.fetchone()
            cursor.close()
            return result is not None
        except Exception as e:
            logger.error(f"Error checking group activation: {e}")
            return False
    
    # Statistics
    def get_stats(self):
        try:
            cursor = self.conn.cursor()
            
            # Total tickets
            cursor.execute('SELECT COUNT(*) FROM tickets')
            total = cursor.fetchone()[0]
            
            # Closed tickets
            cursor.execute('SELECT COUNT(*) FROM tickets WHERE status = %s', ('closed',))
            closed = cursor.fetchone()[0]
            
            # In progress
            cursor.execute('SELECT COUNT(*) FROM tickets WHERE status = %s', ('in_progress',))
            in_progress = cursor.fetchone()[0]
            
            # Pending
            cursor.execute('SELECT COUNT(*) FROM tickets WHERE status = %s', ('pending',))
            pending = cursor.fetchone()[0]
            
            # Spam
            cursor.execute('SELECT COUNT(*) FROM tickets WHERE status = %s', ('spam',))
            spam = cursor.fetchone()[0]
            
            # Admin stats
            cursor.execute('''
                SELECT replied_by_username, COUNT(*) as solved,
                       SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END) as closed_count
                FROM tickets 
                WHERE replied_by_username IS NOT NULL
                GROUP BY replied_by_username
            ''')
            admin_stats = cursor.fetchall()
            
            cursor.close()
            
            return {
                'total': total,
                'closed': closed,
                'in_progress': in_progress,
                'pending': pending,
                'spam': spam,
                'admin_stats': admin_stats
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {
                'total': 0,
                'closed': 0,
                'in_progress': 0,
                'pending': 0,
                'spam': 0,
                'admin_stats': []
            }
    
    # Search
    def search_user(self, query):
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('''
                SELECT DISTINCT u.*
                FROM users u
                WHERE u.user_id::text LIKE %s 
                   OR u.username ILIKE %s 
                   OR u.email ILIKE %s 
                   OR u.phone LIKE %s
            ''', (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))
            users = cursor.fetchall()
            
            # Get tickets for each user
            for user in users:
                cursor.execute('''
                    SELECT * FROM tickets 
                    WHERE user_id = %s 
                    ORDER BY created_at DESC
                ''', (user['user_id'],))
                user['tickets'] = cursor.fetchall()
            
            cursor.close()
            return users
        except Exception as e:
            logger.error(f"Error searching user: {e}")
            return []
    
    # Export data
    def export_all_tickets(self):
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('''
                SELECT 
                    COALESCE(u.first_name, '') || ' ' || COALESCE(u.last_name, '') as name,
                    u.username,
                    u.user_id,
                    t.ticket_id,
                    COALESCE(u.email, 'N/A') as email,
                    COALESCE(u.phone, 'N/A') as phone,
                    t.question as user_question,
                    COALESCE(t.admin_answer, 'No reply yet') as admin_answer,
                    t.status as ticket_status,
                    t.created_at as date_time,
                    COALESCE(t.replied_by_username, 'N/A') as replied_by_admin
                FROM tickets t
                LEFT JOIN users u ON t.user_id = u.user_id
                ORDER BY u.user_id, t.created_at
            ''')
            tickets = cursor.fetchall()
            cursor.close()
            return tickets
        except Exception as e:
            logger.error(f"Error exporting tickets: {e}")
            return []
    
    def export_by_status(self, status):
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('''
                SELECT 
                    COALESCE(u.first_name, '') || ' ' || COALESCE(u.last_name, '') as name,
                    u.username,
                    u.user_id,
                    t.ticket_id,
                    COALESCE(u.email, 'N/A') as email,
                    COALESCE(u.phone, 'N/A') as phone,
                    t.question as user_question,
                    COALESCE(t.admin_answer, 'No reply yet') as admin_answer,
                    t.status as ticket_status,
                    t.created_at as date_time,
                    COALESCE(t.replied_by_username, 'N/A') as replied_by_admin
                FROM tickets t
                LEFT JOIN users u ON t.user_id = u.user_id
                WHERE t.status = %s OR %s = 'all'
                ORDER BY u.user_id, t.created_at
            ''', (status, status))
            tickets = cursor.fetchall()
            cursor.close()
            return tickets
        except Exception as e:
            logger.error(f"Error exporting by status: {e}")
            return []
    
    # Ticket logs
    def get_ticket_logs(self, ticket_id):
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('''
                SELECT * FROM ticket_logs 
                WHERE ticket_id = %s 
                ORDER BY timestamp DESC
            ''', (ticket_id,))
            logs = cursor.fetchall()
            cursor.close()
            return logs
        except Exception as e:
            logger.error(f"Error getting ticket logs: {e}")
            return []
    
    # Delete old data
    def delete_old_data(self, days):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                DELETE FROM tickets 
                WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '%s days'
            ''', (days,))
            deleted = cursor.rowcount
            self.conn.commit()
            cursor.close()
            return deleted
        except Exception as e:
            logger.error(f"Error deleting old data: {e}")
            self.conn.rollback()
            return 0
