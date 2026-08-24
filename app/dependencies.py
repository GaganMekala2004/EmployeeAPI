# Topic: Common Dependencies
from app.database import SessionLocal

# Database Dependency
def get_db():

    # Create a new database session
    db = SessionLocal()

    try:
        # Provide session to the endpoint
        yield db

    finally:
        # Close session after request completes
        db.close()