# ==========================
# Topic: Authentication Routes
# ==========================

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import crud, schemas
from app.dependencies import get_db
from app.models import User
from app.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)

# Configure Logger
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# ==========================
# User Signup
# ==========================
@router.post(
    "/signup",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED
)
def signup(
    user: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    logger.info("Signup attempt for email: %s", user.email)

    existing_user = crud.get_user_by_email(
        db,
        user.email
    )

    if existing_user:
        logger.warning(
            "Signup failed. Email already registered: %s",
            user.email
        )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered."
        )

    hashed_password = hash_password(
        user.password
    )

    db_user = crud.create_user(
        db=db,
        user=user,
        hashed_password=hashed_password
    )

    logger.info(
        "User registered successfully: %s",
        db_user.email
    )

    return db_user


# ==========================
# User Login
# ==========================
@router.post(
    "/login",
    response_model=schemas.Token
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    logger.info(
        f"Login attempt for email: {form_data.username}"
    )

    db_user = crud.get_user_by_email(
        db,
        form_data.username
    )

    if not db_user:

        logger.warning(
            f"Login failed. User not found: {form_data.username}"
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    if not verify_password(
        form_data.password,
        db_user.hashed_password
    ):

        logger.warning(
            f"Login failed. Incorrect password for: {form_data.username}"
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    access_token = create_access_token(
        {
            "sub": db_user.email
        }
    )

    logger.info(
        f"Login successful: {db_user.email}"
    )

    return schemas.Token(
        access_token=access_token,
        token_type="bearer"
    )


# ==========================
# Current Logged-in User
# ==========================
@router.get(
    "/me",
    response_model=schemas.UserResponse
)
def get_logged_in_user(
    current_user: User = Depends(get_current_user)
):
    logger.info(
        f"Profile accessed by user: {current_user.email}"
    )

    return current_user