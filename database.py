import os
import psycopg2
from psycopg2.extras import RealDictCursor
import datetime

class Database:
    def __init__(self):
        self.conn = psycopg2.connect(os.environ['DATABASE_URL'])
        self.create_tables()
    
    def create_tables(self):
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
        
        # Tickets table
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
                closed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Admin groups table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_groups (
                group_id BIGINT PRIMARY KEY,
                added_by BIGINT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Ticket logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ticket_logs (
                log_id SERIAL PRIMARY KEY,
                ticket_id INTEGER,
                action VARCHAR(50),
                admin_id BIGINT,
                admin_username VARCHAR(255),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id)
            )
        ''')
        
        self.conn.commit()
        cursor.close()
    
    # User methods
    def add_user(self, user_id, username, first_name, last_name=None):
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
    
    def update_user_contact(self, user_id, email, phone):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET email = %s, phone = %s
            WHERE user_id = %s
        ''', (email, phone, user_id))
        self.conn.commit()
        cursor.close()
    
    # Ticket methods
    def create_ticket(self, user_id, question):
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
    
    def get_pending_tickets(self):
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('''
            SELECT t.*, u.username, u.first_name, u.last_name, u.email, u.phone
            FROM tickets t
            JOIN users u ON t.user_id = u.user_id
            WHERE t.status IN ('pending', 'in_progress')
            ORDER BY t.created_at DESC
        ''')
        tickets = cursor.fetchall()
        cursor.close()
        return tickets
    
    def get_user_tickets(self, user_id):
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('''
            SELECT * FROM tickets 
            WHERE user_id = %s 
            ORDER BY created_at DESC
        ''', (user_id,))
        tickets = cursor.fetchall()
        cursor.close()
        return tickets
    
    def reply_to_ticket(self, ticket_id, admin_answer, admin_id, admin_username):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE tickets 
            SET admin_answer = %s, 
                replied_by = %s, 
                replied_by_username = %s,
                status = 'closed',
                closed_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE ticket_id = %s AND status != 'closed'
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
    
    def update_ticket_status(self, ticket_id, status, admin_id, admin_username):
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
    
    # Admin group methods
    def add_admin_group(self, group_id, added_by):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO admin_groups (group_id, added_by)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        ''', (group_id, added_by))
        self.conn.commit()
        cursor.close()
    
    def remove_admin_group(self, group_id):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM admin_groups WHERE group_id = %s', (group_id,))
        self.conn.commit()
        cursor.close()
    
    def get_admin_groups(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT group_id FROM admin_groups')
        groups = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return groups
    
    # Statistics
    def get_stats(self):
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
            'admin_stats': admin_stats
        }
    
    # Search
    def search_user(self, query):
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('''
            SELECT DISTINCT u.*, 
                   (SELECT json_agg(t.*) 
                    FROM tickets t 
                    WHERE t.user_id = u.user_id 
                    ORDER BY t.created_at DESC) as tickets
            FROM users u
            WHERE u.user_id::text LIKE %s 
               OR u.username ILIKE %s 
               OR u.email ILIKE %s 
               OR u.phone LIKE %s
        ''', (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))
        results = cursor.fetchall()
        cursor.close()
        return results
    
    # Export data
    def export_all_tickets(self):
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('''
            SELECT u.first_name || ' ' || COALESCE(u.last_name, '') as name,
                   u.username,
                   u.user_id,
                   t.ticket_id,
                   u.email,
                   u.phone,
                   t.question as user_question,
                   t.admin_answer,
                   t.status as ticket_status,
                   t.created_at as date_time,
                   t.replied_by_username as replied_by_admin
            FROM tickets t
            JOIN users u ON t.user_id = u.user_id
            ORDER BY u.user_id, t.created_at
        ''')
        tickets = cursor.fetchall()
        cursor.close()
        return tickets
    
    def export_by_status(self, status):
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('''
            SELECT u.first_name || ' ' || COALESCE(u.last_name, '') as name,
                   u.username,
                   u.user_id,
                   t.ticket_id,
                   u.email,
                   u.phone,
                   t.question as user_question,
                   t.admin_answer,
                   t.status as ticket_status,
                   t.created_at as date_time,
                   t.replied_by_username as replied_by_admin
            FROM tickets t
            JOIN users u ON t.user_id = u.user_id
            WHERE t.status = %s OR %s = 'all'
            ORDER BY u.user_id, t.created_at
        ''', (status, status))
        tickets = cursor.fetchall()
        cursor.close()
        return tickets
    
    # Delete old data
    def delete_old_data(self, days):
        cursor = self.conn.cursor()
        cursor.execute('''
            DELETE FROM tickets 
            WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '%s days'
        ''', (days,))
        deleted = cursor.rowcount
        self.conn.commit()
        cursor.close()
        return deleted
