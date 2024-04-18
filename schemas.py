from pydantic import BaseModel, Field
from typing import Optional


class UserBase(BaseModel):
    nickname: str

    class ConfigDict:
        from_attributes = True


class UserCreate(UserBase):
    password: str

    class ConfigDict:
        from_attributes = True


class User(UserBase):
    user_id: int

    class ConfigDict:
        from_attributes = True


class Login(BaseModel):
    nickname: str
    password: str

    class ConfigDict:
        from_attributes = True


class UserResponse(BaseModel):
    success: bool
    user_id: int = Field(None, alias='user_id')
    nickname: str = Field(None, alias='nickname')
    message: Optional[str] = None

    class ConfigDict:
        from_attributes = True


class UserStatsResponse(BaseModel):
    user_id: int
    wins: int
    losses: int
    draws: int

    class ConfigDict:
        from_attributes = True
