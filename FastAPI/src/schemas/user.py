from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, EmailStr


class UserSchema(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=10)


class UserResponseSchema(BaseModel):
    id: int
    username: str
    email: EmailStr
    avatar: str | None

    model_config = ConfigDict(from_attributes=True)


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RequestEmail(BaseModel):
    email: EmailStr


class UserDb(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    avatar: str | None

    model_config = ConfigDict(from_attributes=True)
