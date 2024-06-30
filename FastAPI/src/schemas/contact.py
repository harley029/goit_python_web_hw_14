from pydantic import BaseModel, ConfigDict, Field, EmailStr
from datetime import date

from src.schemas.user import UserResponseSchema


class ContactSchema(BaseModel):
    first_name: str = Field(min_length=3, max_length=50)
    last_name: str = Field(min_length=3, max_length=50)
    email: EmailStr
    birthday: date
    additional_data: str = Field(max_length=250, json_schema_extra={"nullable": True})

    model_config = ConfigDict(from_attributes=True)


class ContactUpdateSchema(ContactSchema):
    first_name: str
    last_name: str
    email: EmailStr
    birthday: date
    additional_data: str

    model_config = ConfigDict(from_attributes=True)


class ContactResponseSchema(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    birthday: date
    additional_data: str | None
    user: UserResponseSchema | None

    model_config = ConfigDict(from_attributes=True)
