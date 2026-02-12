import time

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from .auth import hash_password
from .database import Base, SessionLocal, engine
from .models import Role, User


def wait_for_db(max_attempts: int = 30, delay_seconds: int = 2) -> None:
    for attempt in range(1, max_attempts + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text('SELECT 1'))
            return
        except OperationalError:
            if attempt == max_attempts:
                raise
            time.sleep(delay_seconds)


def seed():
    wait_for_db()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.email == 'admin@getsendy.dev').first():
            db.add(User(email='admin@getsendy.dev', password_hash=hash_password('password123'), role=Role.ADMIN))
        if not db.query(User).filter(User.email == 'reviewer@getsendy.dev').first():
            db.add(User(email='reviewer@getsendy.dev', password_hash=hash_password('password123'), role=Role.REVIEWER))
        db.commit()
    finally:
        db.close()


if __name__ == '__main__':
    seed()
