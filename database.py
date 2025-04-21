from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

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