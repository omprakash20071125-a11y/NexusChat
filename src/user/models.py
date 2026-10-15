from sqlalchemy import Column, String , Integer, DateTime, Boolean
from src.utils.db import Base
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer,primary_key = True)
    username = Column(String,nullable = False)
    hash_password = Column(String, nullable= False)
    email = Column(String)
    is_online = Column(Boolean, default= False, nullable= False)
    last_seen = Column(DateTime(timezone=True),server_default=func.now(), nullable=True)

    participations = relationship(
      "ConversationParticipant",
      back_populates="user",
      cascade="all, delete-orphan",
  )
    messages = relationship("Message", back_populates="sender")
    message_statuses = relationship("MessageStatus", back_populates="user")