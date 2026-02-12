import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login')
PBKDF2_ITERATIONS = 390000


def _pbkdf2_hash(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, PBKDF2_ITERATIONS)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        scheme, iter_str, salt_b64, hash_b64 = hashed_password.split('$')
        if scheme != 'pbkdf2_sha256':
            return False
        if int(iter_str) != PBKDF2_ITERATIONS:
            return False
        salt = base64.b64decode(salt_b64.encode('ascii'))
        expected = base64.b64decode(hash_b64.encode('ascii'))
    except Exception:
        return False

    candidate = _pbkdf2_hash(plain_password, salt)
    return hmac.compare_digest(candidate, expected)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = _pbkdf2_hash(password, salt)
    return 'pbkdf2_sha256${}${}${}'.format(
        PBKDF2_ITERATIONS,
        base64.b64encode(salt).decode('ascii'),
        base64.b64encode(digest).decode('ascii'),
    )


def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_minutes)
    return jwt.encode({'sub': subject, 'exp': expire}, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        email = payload.get('sub')
        if email is None:
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise credentials_exception
    return user
