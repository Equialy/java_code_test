from datetime import datetime

from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy import Numeric, func,  TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class Wallet(Base):
    __tablename__ = "wallets"

    uuid: Mapped[str] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True, index=True)
    balance: Mapped[int] = mapped_column(Numeric(precision=18, scale=2), nullable=False, default=0 )
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(0), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(0), server_default=func.now(), onupdate=func.now())

