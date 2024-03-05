from typing import Optional
from pydantic import UUID4, BaseModel, Field, EmailStr


class UserBaseSchema(BaseModel):
    email: EmailStr
    first_name: str
    middle_name: str
    last_name: str


class UserSchema(UserBaseSchema):
    id: UUID4
    is_active: bool = Field(default=False)
    refresh_token: Optional[str]
    access_token: Optional[str]

    class Config:
        from_attributes = True


class UserLoginSchema(BaseModel):
    email: EmailStr = Field()
    password: str

class UserLogoutSchema(BaseModel):
    access_token: str
