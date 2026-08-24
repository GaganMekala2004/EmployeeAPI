# ==========================
# Topic: Password Security
# ==========================

import logging
import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app import crud
from app.dependencies import get_db
from app.models import User

# Load Environment Variables
load_dotenv()

# Configure Logger
logger = logging.getLogger(__name__)

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
)

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


# ==========================
# Password Hashing
# ==========================
def hash_password(password: str) -> str:
    logger.info("Hashing password.")
    return pwd_context.hash(password)


# ==========================
# Password Verification
# ==========================
def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:

    is_valid = pwd_context.verify(
        plain_password,
        hashed_password
    )

    if is_valid:
        logger.info("Password verification successful.")
    else:
        logger.warning("Password verification failed.")

    return is_valid


# ==========================
# JWT Creation
# ==========================
def create_access_token(data: dict) -> str:
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update(
        {
            "exp": expire
        }
    )

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    logger.info(
        f"JWT generated for user: {data.get('sub')}"
    )

    return encoded_jwt


# ==========================
# Get Current User
# ==========================
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    logger.info("Validating JWT token.")

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        email = payload.get("sub")

        if email is None:
            logger.warning("JWT does not contain subject (sub).")
            raise credentials_exception

        logger.info(
            f"JWT validated successfully for user: {email}"
        )

    except JWTError:
        logger.warning("Invalid or expired JWT received.")
        raise credentials_exception

    user = crud.get_user_by_email(
        db,
        email
    )

    if user is None:
        logger.warning(
            f"User not found for token: {email}"
        )
        raise credentials_exception

    if not user.is_active:
        logger.warning(
            f"Inactive user attempted access: {email}"
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user."
        )

    logger.info(
        f"Authenticated user: {user.email}"
    )

    return user


# ==========================
# Admin Authorization
# ==========================
def require_admin(
    current_user: User = Depends(get_current_user)
):
    logger.info(
        f"Checking admin privileges for {current_user.email}"
    )

    if current_user.role != "admin":

        logger.warning(
            f"Access denied. {current_user.email} attempted admin-only operation."
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can perform this action."
        )

    logger.info(
        f"Admin access granted to {current_user.email}"
    )

    return current_user