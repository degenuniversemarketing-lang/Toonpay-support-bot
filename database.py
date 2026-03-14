import os
import psycopg2
from psycopg2.extras import RealDictCursor
import datetime
import logging
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.conn = None
        self.connect()
        if self.conn:
            self.fix_schema()
            self.create_tables()
    
    def connect(self):
        """Establish database connection"""
        try:
            database_url = os.environ.get('DATABASE_URL')
            if not database_url:
                logger.error("DATABASE_URL environment variable not set!")
                return False
            
            logger.info(f"Connecting to database...")
            self.conn = psycopg2.connect(database_url)
            logger.info("Database connection successful")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def fix_schema(self):
        """Fix existing schema if there are issues"""
        cursor = None
        try:
            cursor = self.conn.cursor()
            
            # Check if tickets table exists and has the correct structure
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'tickets'
                )
            """)
            table_exists = cursor.fetchone()[0]
            
            if table_exists:
                logger.info("Checking tickets table schema...")
                
                # Check if ticket_id column exists as SERIAL
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = 'tickets' AND column_name = 'ticket_id'
                    )
                """)
                has_ticket_id = cursor.fetchone()[0]
                
                if not has_ticket_id:
                    logger.warning("ticket_id column missing! Recreating tickets table...")
                    
                    # Drop and recreate tickets table
                    cursor.execute("DROP TABLE IF EXISTS ticket_logs CASCADE")
                    cursor.execute("DROP TABLE IF EXISTS tickets CASCADE")
                    logger.info("Dropped old tickets table")
                    
                # Check if ticket_id is SERIAL
                else:
                    cursor.execute("""
                        SELECT data_type 
                        FROM information_schema.columns 
                        WHERE table_name = 'tickets' AND column_name = 'ticket_id'
                    """)
                    data_type = cursor.fetchone()[0]
                    logger.info(f"ticket_id data type: {data_type}")
            
            self.conn.commit()
            logger.info("Schema check completed")
            
        except Exception as e:
            logger.error(f"Error fixing schema: {e}")
            logger.error(traceback.format_exc())
            self.conn.rollback()
        finally:
            if cursor:
                cursor.close()
    
    def create_tables(self):
        """Create all necessary tables if they don't exist"""
        if not self.conn:
            logger.error("No database connection for table creation")
            return False
        
        cursor = None
        try:
            cursor = self.conn.cursor()
            
            # Users table
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
            
            # Admin groups table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_groups (
                    group_id BIGINT PRIMARY KEY,
                    added_by BIGINT,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            logger.info("Admin groups table created/verified")
            
            # Activated groups table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS activated_groups (
                    group_id BIGINT PRIMARY KEY,
                    activated_by BIGINT,
                    activated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            logger.info("Activated groups table created/verified")
            
            # Tickets table - Make sure ticket_id is SERIAL PRIMARY KEY
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
            
            # Ticket logs table
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
            
            # Custom commands table (NEW)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS custom_commands (
                    command VARCHAR(50) PRIMARY KEY,
                    content TEXT,
                    added_by BIGINT,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            logger.info("Custom commands table created/verified")
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tickets_user_id ON tickets(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tickets_created_at ON tickets(created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ticket_logs_ticket_id ON ticket_logs(ticket_id)')
            logger.info("Indexes created/verified")
            
            self.conn.commit()
            logger.info("Database initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            logger.error(traceback.format_exc())
            if self.conn:
                self.conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
    
    # User methods
    def add_user(self, user_id, username, first_name, last_name=None):
        """Add or update a user"""
        if not self.conn:
            logger.error("No database connection for add_user")
            return False
        
        cursor = None
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO users (user_id, username, first_name, last_name)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id) 
                DO UPDATE SET username = EXCLUDED.username,
                             first_name = EXCLUDED.first_name,
                             last_name = EXCLUDED.last_name
                RETURNING user_id
            ''', (user_id, username, first_name, last_name))
            
            result = cursor.fetchone()
            self.conn.commit()
            logger.info(f"User {user_id} added/updated successfully")
            return result is not None
            
        except Exception as e:
            logger.error(f"Error adding user {user_id}: {e}")
            logger.error(traceback.format_exc())
            if self.conn:
                self.conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
    
    def update_user_contact(self, user_id, email, phone, name=None):
        """Update user contact information with optional name"""
        if not self.conn:
            logger.error("No database connection for update_user_contact")
            return False
        
        cursor = None
        try:
            cursor = self.conn.cursor()
            
            if name:
                # Split name into first and last name
                name_parts = name.split(' ', 1)
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else ''
                
                cursor.execute('''
                    UPDATE users 
                    SET email = %s, phone = %s, first_name = %s, last_name = %s
                    WHERE user_id = %s
                    RETURNING user_id
                ''', (email, phone, first_name, last_name, user_id))
                logger.info(f"Updated user {user_id} with name: {first_name} {last_name}")
            else:
                cursor.execute('''
                    UPDATE users 
                    SET email = %s, phone = %s
                    WHERE user_id = %s
                    RETURNING user_id
                ''', (email, phone, user_id))
            
            result = cursor.fetchone()
            self.conn.commit()
            
            if result:
                logger.info(f"Contact info updated for user {user_id}")
                return True
            else:
                logger.warning(f"User {user_id} not found for contact update")
                return False
                
        except Exception as e:
            logger.error(f"Error updating user contact for {user_id}: {e}")
            logger.error(traceback.format_exc())
            if self.conn:
                self.conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
    
    def get_user(self, user_id):
        """Get user by ID"""
        if not self.conn:
            logger.error("No database connection for get_user")
            return None
        
        cursor = None
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
            user = cursor.fetchone()
            return user
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
    
    # Admin groups methods
    def add_admin_group(self, group_id, added_by):
        """Add an admin group"""
        if not self.conn:
            logger.error("No database connection for add_admin_group")
            return False
        
        cursor = None
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO admin_groups (group_id, added_by)
                VALUES (%s, %s)
                ON CONFLICT (group_id) DO NOTHING
                RETURNING group_id
            ''', (group_id, added_by))
            
            result = cursor.fetchone()
            self.conn.commit()
            return result is not None
        except Exception as e:
            logger.error(f"Error adding admin group {group_id}: {e}")
            self.conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
    
    def remove_admin_group(self, group_id):
        """Remove an admin group"""
        if not self.conn:
            logger.error("No database connection for remove_admin_group")
            return False
        
        cursor = None
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM admin_groups WHERE group_id = %s', (group_id,))
            deleted = cursor.rowcount
            self.conn.commit()
            return deleted > 0
        except Exception as e:
            logger.error(f"Error removing admin group {group_id}: {e}")
            self.conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
    
    def get_admin_groups(self):
        """Get all admin groups (legacy method)"""
        if not self.conn:
            logger.error("No database connection for get_admin_groups")
            return []
        
        cursor = None
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT group_id FROM admin_groups')
            groups = [row[0] for row in cursor.fetchall()]
            logger.info(f"Found {len(groups)} admin groups")
            return groups
        except Exception as e:
            logger.error(f"Error getting admin groups: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
    
    # Activated groups methods (for /support command)
    def activate_group(self, group_id, activated_by):
        """Activate a group for /support command"""
        if not self.conn:
            logger.error("No database connection for activate_group")
            return False
        
        cursor = None
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO activated_groups (group_id, activated_by)
                VALUES (%s, %s)
                ON CONFLICT (group_id) DO NOTHING
                RETURNING group_id
            ''', (group_id, activated_by))
            
            result = cursor.fetchone()
            self.conn.commit()
            return result is not None
        except Exception as e:
            logger.error(f"Error activating group {group_id}: {e}")
            self.conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()

    def deactivate_group(self, group_id):
        """Deactivate a group"""
        if not self.conn:
            logger.error("No database connection for deactivate_group")
            return False
        
        cursor = None
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM activated_groups WHERE group_id = %s', (group_id,))
            deleted = cursor.rowcount
            self.conn.commit()
            return deleted > 0
        except Exception as e:
            logger.error(f"Error deactivating group {group_id}: {e}")
            self.conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()

    def get_activated_groups(self):
        """Get all activated groups"""
        if not self.conn:
            logger.error("No database connection for get_activated_groups")
            return []
        
        cursor = None
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT group_id FROM activated_groups')
            groups = [row[0] for row in cursor.fetchall()]
            return groups
        except Exception as e:
            logger.error(f"Error getting activated groups: {e}")
            return []
        finally:
            if cursor:
                cursor.close()

    def is_group_activated(self, group_id):
        """Check if a group is activated"""
        if not self.conn:
            logger.error("No database connection for is_group_activated")
            return False
        
        cursor = None
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT 1 FROM activated_groups WHERE group_id = %s', (group_id,))
            result = cursor.fetchone()
            return result is not None
        except Exception as e:
            logger.error(f"Error checking group activation for {group_id}: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
    
    # Custom commands methods (NEW)
    def add_custom_command(self, command, content, added_by):
        """Add a custom command"""
        if not self.conn:
            logger.error("No database connection for add_custom_command")
            return False
        
        cursor = None
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO custom_commands (command, content, added_by)
                VALUES (%s, %s, %s)
                ON CONFLICT (command) DO UPDATE SET 
                    content = EXCLUDED.content,
                    added_by = EXCLUDED.added_by
                RETURNING command
            ''', (command, content, added_by))
            
            result = cursor.fetchone()
            self.conn.commit()
            return result is not None
        except Exception as e:
            logger.error(f"Error adding custom command: {e}")
            self.conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()

    def get_custom_command(self, command):
        """Get a custom command content"""
        if not self.conn:
            logger.error("No database connection for get_custom_command")
            return None
        
        cursor = None
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SELECT * FROM custom_commands WHERE command = %s', (command,))
            result = cursor.fetchone()
            return result
        except Exception as e:
            logger.error(f"Error getting custom command: {e}")
            return None
        finally:
            if cursor:
                cursor.close()

    def get_custom_commands(self):
        """Get all custom commands"""
        if not self.conn:
            logger.error("No database connection for get_custom_commands")
            return []
        
        cursor = None
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SELECT * FROM custom_commands ORDER BY command')
            results = cursor.fetchall()
            return results
        except Exception as e:
            logger.error(f"Error getting custom commands: {e}")
            return []
        finally:
            if cursor:
                cursor.close()

    def remove_custom_command(self, command):
        """Remove a custom command"""
        if not self.conn:
            logger.error("No database connection for remove_custom_command")
            return False
        
        cursor = None
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM custom_commands WHERE command = %s', (command,))
            deleted = cursor.rowcount
            self.conn.commit()
            return deleted > 0
        except Exception as e:
            logger.error(f"Error removing custom command: {e}")
            self.conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
    
    # Broadcast methods (NEW)
    def get_all_users(self):
        """Get all users for broadcasting"""
        if not self.conn:
            logger.error("No database connection for get_all_users")
            return []
        
        cursor = None
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SELECT user_id FROM users ORDER BY created_at DESC')
            users = cursor.fetchall()
            return users
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []
        finally:
            if cursor:
                cursor.close()

    def get_all_users_with_stats(self):
        """Get all users with their ticket statistics"""
        if not self.conn:
            logger.error("No database connection for get_all_users_with_stats")
            return []
        
        cursor = None
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('''
                SELECT 
                    u.user_id,
                    u.username,
                    u.first_name,
                    u.last_name,
                    u.email,
                    u.phone,
                    u.created_at,
                    COUNT(t.ticket_id) as total_tickets,
                    SUM(CASE WHEN t.status = 'closed' THEN 1 ELSE 0 END) as solved_tickets,
                    SUM(CASE WHEN t.status IN ('pending', 'in_progress') THEN 1 ELSE 0 END) as in_progress_tickets,
                    SUM(CASE WHEN t.status = 'spam' THEN 1 ELSE 0 END) as spam_tickets
                FROM users u
                LEFT JOIN tickets t ON u.user_id = t.user_id
                GROUP BY u.user_id, u.username, u.first_name, u.last_name, u.email, u.phone, u.created_at
                ORDER BY u.created_at DESC
            ''')
            users = cursor.fetchall()
            
            # Format name
            for user in users:
                user['name'] = f"{user['first_name']} {user.get('last_name', '')}".strip()
            
            return users
        except Exception as e:
            logger.error(f"Error getting users with stats: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
    
    # Ticket methods
    def create_ticket(self, user_id, question):
        """Create a new ticket"""
        if not self.conn:
            logger.error("No database connection for create_ticket")
            return None
        
        cursor = None
        try:
            cursor = self.conn.cursor()
            
            cursor.execute('''
                INSERT INTO tickets (user_id, question, status)
                VALUES (%s, %s, 'pending')
                RETURNING ticket_id
            ''', (user_id, question))
            
            result = cursor.fetchone()
            if result and len(result) > 0:
                ticket_id = result[0]
                self.conn.commit()
                logger.info(f"Ticket {ticket_id} created for user {user_id}")
                return ticket_id
            else:
                logger.error(f"No ticket_id returned from INSERT for user {user_id}")
                self.conn.rollback()
                return None
                
        except psycopg2.errors.UndefinedColumn as e:
            logger.error(f"Database schema error - missing column: {e}")
            logger.error("Attempting to fix schema...")
            
            # Try to fix the schema
            try:
                # Drop and recreate tickets table
                cursor.execute("DROP TABLE IF EXISTS ticket_logs CASCADE")
                cursor.execute("DROP TABLE IF EXISTS tickets CASCADE")
                cursor.execute('''
                    CREATE TABLE tickets (
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
                self.conn.commit()
                logger.info("Schema fixed, retrying ticket creation...")
                
                # Retry the insert
                cursor.execute('''
                    INSERT INTO tickets (user_id, question, status)
                    VALUES (%s, %s, 'pending')
                    RETURNING ticket_id
                ''', (user_id, question))
                
                result = cursor.fetchone()
                if result:
                    ticket_id = result[0]
                    self.conn.commit()
                    logger.info(f"Ticket {ticket_id} created for user {user_id} after schema fix")
                    return ticket_id
                    
            except Exception as fix_error:
                logger.error(f"Failed to fix schema: {fix_error}")
                self.conn.rollback()
                return None
                
        except Exception as e:
            logger.error(f"Error creating ticket for user {user_id}: {e}")
            logger.error(traceback.format_exc())
            if self.conn:
                self.conn.rollback()
            return None
        finally:
            if cursor:
                cursor.close()
    
    def get_pending_tickets(self):
        """Get all pending and in-progress tickets"""
        if not self.conn:
            logger.error("No database connection for get_pending_tickets")
            return []
        
        cursor = None
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
            logger.info(f"Found {len(tickets)} pending tickets")
            return tickets
        except Exception as e:
            logger.error(f"Error getting pending tickets: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
    
    def get_user_tickets(self, user_id):
        """Get all tickets for a specific user"""
        if not self.conn:
            logger.error("No database connection for get_user_tickets")
            return []
        
        cursor = None
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('''
                SELECT * FROM tickets 
                WHERE user_id = %s 
                ORDER BY created_at DESC
            ''', (user_id,))
            tickets = cursor.fetchall()
            logger.info(f"Found {len(tickets)} tickets for user {user_id}")
            return tickets
        except Exception as e:
            logger.error(f"Error getting user tickets for {user_id}: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
    
    def get_ticket(self, ticket_id):
        """Get ticket by ID"""
        if not self.conn:
            logger.error("No database connection for get_ticket")
            return None
        
        cursor = None
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('''
                SELECT t.*, u.username, u.first_name, u.last_name, u.email, u.phone
                FROM tickets t
                LEFT JOIN users u ON t.user_id = u.user_id
                WHERE t.ticket_id = %s
            ''', (ticket_id,))
            ticket = cursor.fetchone()
            return ticket
        except Exception as e:
            logger.error(f"Error getting ticket {ticket_id}: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
    
    def reply_to_ticket(self, ticket_id, admin_answer, admin_id, admin_username):
        """Reply to a ticket and close it"""
        if not self.conn:
            logger.error("No database connection for reply_to_ticket")
            return False
        
        cursor = None
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
                logger.info(f"Ticket {ticket_id} replied by {admin_username}")
                return True
            else:
                logger.warning(f"Ticket {ticket_id} update returned no rows")
                self.conn.rollback()
                return False
            
        except Exception as e:
            logger.error(f"Error replying to ticket {ticket_id}: {e}")
            logger.error(traceback.format_exc())
            if self.conn:
                self.conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
    
    def update_ticket_status(self, ticket_id, status, admin_id, admin_username):
        """Update ticket status"""
        if not self.conn:
            logger.error("No database connection for update_ticket_status")
            return False
        
        cursor = None
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE tickets 
                SET status = %s, 
                    replied_by = %s, 
                    replied_by_username = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE ticket_id = %s
                RETURNING ticket_id
            ''', (status, admin_id, admin_username, ticket_id))
            
            result = cursor.fetchone()
            
            if result:
                # Log the action
                cursor.execute('''
                    INSERT INTO ticket_logs (ticket_id, action, admin_id, admin_username)
                    VALUES (%s, %s, %s, %s)
                ''', (ticket_id, status, admin_id, admin_username))
                self.conn.commit()
                logger.info(f"Ticket {ticket_id} status updated to {status} by {admin_username}")
                return True
            else:
                logger.warning(f"Ticket {ticket_id} status update returned no rows")
                self.conn.rollback()
                return False
                
        except Exception as e:
            logger.error(f"Error updating ticket status for {ticket_id}: {e}")
            logger.error(traceback.format_exc())
            if self.conn:
                self.conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
    
    # Statistics
    def get_stats(self):
        """Get bot statistics"""
        if not self.conn:
            logger.error("No database connection for get_stats")
            return {
                'total': 0,
                'closed': 0,
                'in_progress': 0,
                'pending': 0,
                'spam': 0,
                'admin_stats': []
            }
        
        cursor = None
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
                SELECT 
                    COALESCE(replied_by_username, 'Unknown') as admin,
                    COUNT(*) as solved,
                    SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END) as closed_count
                FROM tickets 
                WHERE replied_by_username IS NOT NULL
                GROUP BY replied_by_username
            ''')
            admin_stats = cursor.fetchall()
            
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
        finally:
            if cursor:
                cursor.close()
    
    # Search
    def search_user(self, query):
        """Search users by various fields"""
        if not self.conn:
            logger.error("No database connection for search_user")
            return []
        
        cursor = None
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
            
            return users
        except Exception as e:
            logger.error(f"Error searching user with query '{query}': {e}")
            return []
        finally:
            if cursor:
                cursor.close()
    
    # Export data
    def export_all_tickets(self):
        """Export all tickets for Excel download"""
        if not self.conn:
            logger.error("No database connection for export_all_tickets")
            return []
        
        cursor = None
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
            return tickets
        except Exception as e:
            logger.error(f"Error exporting tickets: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
    
    def export_by_status(self, status):
        """Export tickets by status"""
        if not self.conn:
            logger.error("No database connection for export_by_status")
            return []
        
        cursor = None
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
            return tickets
        except Exception as e:
            logger.error(f"Error exporting by status {status}: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
    
    # Ticket logs
    def get_ticket_logs(self, ticket_id):
        """Get logs for a specific ticket"""
        if not self.conn:
            logger.error("No database connection for get_ticket_logs")
            return []
        
        cursor = None
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('''
                SELECT * FROM ticket_logs 
                WHERE ticket_id = %s 
                ORDER BY timestamp DESC
            ''', (ticket_id,))
            logs = cursor.fetchall()
            return logs
        except Exception as e:
            logger.error(f"Error getting ticket logs for {ticket_id}: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
    
    # Delete old data (UPDATED to support fractional days)
    def delete_old_data(self, days):
        """Delete tickets older than specified days (supports fractional days)"""
        if not self.conn:
            logger.error("No database connection for delete_old_data")
            return 0
        
        cursor = None
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                DELETE FROM tickets 
                WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '%s seconds'
                RETURNING ticket_id
            ''', (days * 86400,))  # Convert days to seconds
            deleted = cursor.rowcount
            self.conn.commit()
            logger.info(f"Deleted {deleted} tickets older than {days} days")
            return deleted
        except Exception as e:
            logger.error(f"Error deleting old data: {e}")
            if self.conn:
                self.conn.rollback()
            return 0
        finally:
            if cursor:
                cursor.close()
    
    # Health check
    def check_connection(self):
        """Check if database connection is alive"""
        if not self.conn:
            return False
        
        cursor = None
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT 1')
            cursor.fetchone()
            return True
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
