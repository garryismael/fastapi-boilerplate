from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.domain.base_entities import UUID, PersistentDeletion, Timestamp


class UserBase(BaseModel):
    name: Annotated[str, Field(min_length=2, max_length=50, examples=["User Userson"])]
    username: Annotated[
        str,
        Field(
            min_length=2, max_length=20, pattern=r"^[a-z0-9]+$", examples=["userson"]
        ),
    ]
    email: Annotated[EmailStr, Field(examples=["user.userson@example.com"])]


class UserDB(Timestamp, UserBase, UUID, PersistentDeletion):
    hashed_password: str


class User(UserBase):
    id: int
    hashed_password: str
    is_superuser: bool


class UserRead(BaseModel):
    id: int

    name: Annotated[str, Field(min_length=2, max_length=50, examples=["User Userson"])]
    username: Annotated[
        str,
        Field(
            min_length=2, max_length=20, pattern=r"^[a-z0-9]+$", examples=["userson"]
        ),
    ]
    email: Annotated[EmailStr, Field(examples=["user.userson@example.com"])]
    is_superuser: bool


class PaginatedListUserRead(BaseModel):
    data: list[UserRead]
    total_count: int
    has_more: bool
    page: int
    items_per_page: int


class UserCreate(UserBase):
    model_config = ConfigDict(extra="forbid")

    is_superuser: bool
    password: Annotated[
        str,
        Field(
            pattern=r"^.{8,}|[0-9]+|[A-Z]+|[a-z]+|[^a-zA-Z0-9]+$",
            examples=["Str1ngst!"],
        ),
    ]


class UserCreateInternal(UserBase):
    hashed_password: str


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Annotated[
        str | None,
        Field(min_length=2, max_length=50, examples=["User Userberg"], default=None),
    ]
    username: Annotated[
        str | None,
        Field(
            min_length=2,
            max_length=20,
            pattern=r"^[a-z0-9]+$",
            examples=["userberg"],
            default=None,
        ),
    ]
    email: Annotated[
        EmailStr | None, Field(examples=["user.userberg@example.com"], default=None)
    ]


class UserUpdateInternal(UserUpdate):
    updated_at: datetime


class UserDelete(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_deleted: bool
    deleted_at: datetime


class UserRestoreDeleted(BaseModel):
    is_deleted: bool


class UserUpdatePassword(BaseModel):
    hashed_password: str
