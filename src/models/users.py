import uuid
from src.utils.db import Base
from sqlalchemy import (
    Boolean,
    Column,
    UUID,
    LargeBinary,
    PrimaryKeyConstraint,
    String,
    UniqueConstraint,
)


class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True), nullable=False, primary_key=True, default=uuid.uuid4
    )
    email = Column(String(225), nullable=False, unique=True)
    first_name = Column(String(225))
    middle_name = Column(String(225))
    last_name = Column(String(225))
    hashed_password = Column(LargeBinary, nullable=False)
    refresh_token = Column(String(225))
    access_token = Column(String(225))
    is_active = Column(Boolean, default=False)

    UniqueConstraint("email", name="uq_user_email")
    PrimaryKeyConstraint("id", name="pk_user_id")

    def __repr__(self):
        """Returns string representation of model instance"""
        return "<User {first_name}>".format(first_name=self.first_name)
