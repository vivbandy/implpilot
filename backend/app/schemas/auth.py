"""Authentication Pydantic schemas."""
from uuid import UUID

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Schema for login request."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """
    Schema for JWT token payload data.

    This is the data encoded inside the JWT token.
    """
    user_id: UUID | None = None
    email: str | None = None
