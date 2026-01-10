from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from ..db import get_db
from ..schemas import UserCreate, UserResponse, UserLogin, Token, TokenData
from ..services.userservice import UserService
from ..exceptions import (
    UserAlreadyExistsError,
    InvalidCredentialsError,
    UserNotFoundError,
)


router = APIRouter()
user_service = UserService()


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Register a new user.

    Creates a new user account with the provided username, email, and password.
    The password is automatically hashed using Argon2.

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        UserResponse: User data without password hash

    Raises:
        409 Conflict: If username or email already exists
        422 Unprocessable Entity: If validation fails
    """
    try:
        db_user = await user_service.create_user(db, user_data)
        return db_user
    except UserAlreadyExistsError as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user",
        )


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
async def login_user(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    Authenticate user and return JWT token.

    Validates user credentials and returns a JWT access token if successful.

    Args:
        login_data: Login credentials (username and password)
        db: Database session

    Returns:
        Token: JWT access token and token type

    Raises:
        401 Unauthorized: If credentials are invalid or user is inactive
        422 Unprocessable Entity: If validation fails
    """
    try:
        user = await user_service.authenticate_user(db, login_data)

        # Create JWT token
        access_token = user_service.security.create_access_token(
            data={"sub": user.username}
        )

        return Token(access_token=access_token, token_type="bearer")

    except InvalidCredentialsError as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed",
        )


@router.post("/verify", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def verify_token(token_data: TokenData, db: AsyncSession = Depends(get_db)):
    """
    Verify JWT token and return user information.

    Validates the provided JWT token and returns the associated user data.

    Args:
        token_data: Token data containing the JWT token
        db: Database session

    Returns:
        UserResponse: User data without password hash

    Raises:
        401 Unauthorized: If token is invalid or expired
        404 Not Found: If user not found
        422 Unprocessable Entity: If validation fails
    """
    if not token_data.token:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Token is required"
        )

    try:
        user = await user_service.get_current_user_by_token(db, token_data.token)
        return UserResponse.model_validate(user)

    except (InvalidCredentialsError, UserNotFoundError) as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token verification failed",
        )


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_current_user(
    authorization: Optional[str] = Header(None), db: AsyncSession = Depends(get_db)
):
    """
    Get current authenticated user from Authorization header.

    Returns the current user's information based on the JWT token
    provided in the Authorization header.

    Args:
        authorization: Authorization header (Bearer <token>)
        db: Database session

    Returns:
        UserResponse: Current user data

    Raises:
        401 Unauthorized: If token is invalid or user not found
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing or invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ")[1]

    try:
        user = await user_service.get_current_user_by_token(db, token)
        return user
    except (InvalidCredentialsError, UserNotFoundError) as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get current user",
        )
