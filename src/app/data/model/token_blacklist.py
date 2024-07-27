from datetime import datetime

from app.data.database import Base
from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column


class TokenBlacklistModel(Base):
    __tablename__ = "token_blacklist"

    id: Mapped[int] = mapped_column(
        "id",
        autoincrement=True,
        nullable=False,
        unique=True,
        primary_key=True,
        init=False,
    )
    token: Mapped[str] = mapped_column(String, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
