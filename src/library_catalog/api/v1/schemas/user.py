from uuid import UUID
from pydantic import BaseModel, Field, field_validator, EmailStr


class UserCreate(BaseModel):

    username: str = Field(..., min_length=3, max_length=50,)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128,)

class UserLogin(BaseModel):

    username: str
    password: str

class UserPublic(BaseModel):

    id: UUID
    username: str
    email: EmailStr
    role: str

    model_config = {"from_attributes": True}

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
