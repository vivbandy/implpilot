"""Authentication endpoints: login, logout, get current user."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import UserResponse
from app.services import auth_service
from app.utils.dependencies import get_current_user


router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Login endpoint - authenticate user and return JWT token.

    Args:
        login_data: Email and password
        db: Database session

    Returns:
        JWT access token

    Raises:
        HTTPException: 401 if credentials are invalid
    """
    user = await auth_service.authenticate_user(
        db,
        login_data.email,
        login_data.password,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token with user data
    access_token = auth_service.create_access_token(
        data={
            "user_id": str(user.id),
            "email": user.email,
        }
    )

    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Get current authenticated user.

    This is a protected endpoint that requires a valid JWT token.

    Args:
        current_user: Injected by get_current_user dependency

    Returns:
        Current user information
    """
    return current_user


@router.post("/logout")
async def logout():
    """
    Logout endpoint.

    Since we're using stateless JWT tokens, logout is handled client-side
    by removing the token. This endpoint exists for API completeness and
    could be extended in the future to implement token blacklisting.

    Returns:
        Success message
    """
    return {"message": "Successfully logged out"}
