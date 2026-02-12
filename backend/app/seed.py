from .auth import hash_password
from .database import Base, SessionLocal, engine
from .models import Role, User


def seed():
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
