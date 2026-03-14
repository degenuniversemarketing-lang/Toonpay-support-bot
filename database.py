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
