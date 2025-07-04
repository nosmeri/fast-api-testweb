from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from config.db import Base
from pydantic import BaseModel, ConfigDict
from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .refresh_tocken import RefreshToken


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid4())
    )

    username: Mapped[str] = mapped_column(
        String, unique=True, index=True, nullable=False
    )
    password: Mapped[str] = mapped_column(String, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )


class UserCreate(BaseModel):
    username: str
    password: str


class UserLogin(UserCreate):
    pass


class ChangePassword(BaseModel):
    currentPassword: str
    newPassword: str


class UserResponse(BaseModel):
    id: str
    username: str
    is_admin: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
