from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from src.config import Config
import logging

logger = logging.getLogger(__name__)

# Create engine
engine = create_engine(Config.DATABASE_URL)
db_session = scoped_session(sessionmaker(bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    """Initialize database and create tables"""
    import src.models
    
    # Import all models to ensure they're registered with Base
    from src.models import User, Ticket, TicketReply, AllowedGroup
    
    # Drop all tables (THIS WILL DELETE ALL DATA - but we need to fix the ENUM issue)
    logger.warning("Dropping all existing tables to fix ENUM issue...")
    Base.metadata.drop_all(bind=engine)
    
    # Create fresh tables
    logger.info("Creating fresh database tables with correct schema...")
    Base.metadata.create_all(bind=engine)
    
    # Verify tables were created
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    logger.info(f"Created tables: {tables}")
    
    if 'tickets' in tables:
        columns = [col['name'] for col in inspector.get_columns('tickets')]
        logger.info(f"Tickets table columns: {columns}")
        
        # Check if status column exists and its type
        status_column = next((col for col in inspector.get_columns('tickets') if col['name'] == 'status'), None)
        if status_column:
            logger.info(f"Status column type: {status_column['type']}")
        
    logger.info("✅ Database initialization complete")
