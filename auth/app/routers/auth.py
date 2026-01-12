from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from shared.events import LoginMethod
from ..db import get_db
from ..schemas import (
    UserCreate,
    UserResponse,
    UserLogin,
    TokenData,
    TokenResponse,
    RefreshTokenRequest,
)
from ..services.userservice import UserService
from ..services.eventpublisher import EventPublisher
from ..exceptions import (
    UserAlreadyExistsError,
    InvalidCredentialsError,
    UserNotFoundError,
    InvalidRefreshTokenError,
)


router = APIRouter()
user_service = UserService()


def get_event_publisher() -> EventPublisher:
    from ..main import event_publisher

    return event_publisher


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    event_pub: EventPublisher = Depends(get_event_publisher),
):
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

        await event_pub.publish_user_registered(db_user)

        return db_user
    except UserAlreadyExistsError as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user",
        )


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login_user(
    login_data: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db),
    event_pub: EventPublisher = Depends(get_event_publisher),
):
    """
    Authenticate user and return JWT access token with refresh token.

    Validates user credentials and returns both access and refresh tokens if successful.
    Access tokens expire in 30 minutes, refresh tokens expire in 7 days.

    Args:
        login_data: Login credentials (username and password)
        db: Database session

    Returns:
        TokenResponse: JWT access token, refresh token, and expiration info

    Raises:
        401 Unauthorized: If credentials are invalid or user is inactive
        422 Unprocessable Entity: If validation fails
    """
    try:
        user = await user_service.authenticate_user(db, login_data)

        refresh_token_obj = await user_service.create_refresh_token(db, user.id)
        access_token = user_service.security.create_access_token(
            data={"sub": user.username}
        )

        await event_pub.publish_user_authenticated(
            user=user, method=LoginMethod.EMAIL_PASSWORD, request=request
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_obj.token,
            expires_in=1800,
        )

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


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Exchange refresh token for new access and refresh tokens.

    Validates the refresh token and returns new tokens. The old refresh token
    is automatically revoked for security.

    Args:
        refresh_request: Request containing the refresh token
        db: Database session

    Returns:
        TokenResponse: New access token, refresh token, and expiration info

    Raises:
        401 Unauthorized: If refresh token is invalid, expired, or revoked
        422 Unprocessable Entity: If validation fails
    """
    try:
        token_response, user = await user_service.refresh_access_token_with_user(
            db, refresh_request.refresh_token
        )

        return token_response
    except InvalidRefreshTokenError as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed",
        )
