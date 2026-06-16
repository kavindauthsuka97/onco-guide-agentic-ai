# Import database engine
from app.db.database import engine

# Import database base class
from app.db.database import Base

# Import models so SQLAlchemy knows them
from app.db import models


# Initialize database tables
def init_database():

    # Create all tables if they do not exist
    Base.metadata.create_all(bind=engine)


# Run when executed directly
if __name__ == "__main__":

    # Create database tables
    init_database()

    # Print success message
    print("Database tables created successfully.")