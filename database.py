import os
import logging
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

def init_db(app):
    db.init_app(app)
    
    with app.app_context():
        # Import models here to ensure they're registered with SQLAlchemy
        import models
        
        # Create all tables
        db.create_all()
        
        # Check for missing columns and add them if needed
        try:
            ensure_ssh_columns_exist()
        except Exception as e:
            logging.error(f"Error ensuring SSH columns exist: {str(e)}")
            
def ensure_ssh_columns_exist():
    """
    Check if SSH columns exist in the user_settings table and add them if they don't
    """
    with db.engine.connect() as conn:
        # Check if ssh_host column exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='user_settings' AND column_name='ssh_host'
        """))
        
        ssh_host_exists = result.fetchone() is not None
        
        if not ssh_host_exists:
            logging.info("Adding SSH columns to user_settings table")
            # Add the missing columns
            conn.execute(text("""
                ALTER TABLE user_settings 
                ADD COLUMN ssh_host VARCHAR(255),
                ADD COLUMN ssh_user VARCHAR(255),
                ADD COLUMN ssh_password VARCHAR(255),
                ADD COLUMN ssh_key_path VARCHAR(255)
            """))
            conn.commit()
            logging.info("SSH columns added successfully")
        else:
            logging.info("SSH columns already exist in user_settings table")