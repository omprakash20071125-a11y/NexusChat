from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from src.utils.db import Base


class Conversation(Base):
  __tablename__ = "conversations"

  id = Column(Integer, primary_key=True, index=True)
  is_group = Column(Boolean, default=False)
  name = Column(String, nullable=True)  # Null for DMs, required for groups
  created_at = Column(DateTime, default=datetime.utcnow)

  # Relationships
  participants = relationship(
      "ConversationParticipant",
      back_populates="conversation",
      cascade="all, delete-orphan",
  )
  messages = relationship(
      "Message", back_populates="conversation", cascade="all, delete-orphan"
  )


class ConversationParticipant(Base):
  __tablename__ = "conversation_participants"

  id = Column(Integer, primary_key=True, index=True)
  user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
  conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
  joined_at = Column(DateTime, default=datetime.utcnow)

  # FIX: Change "User" to "UserModel"
  user = relationship("UserModel", back_populates="participations")
  conversation = relationship("Conversation", back_populates="participants")


class Message(Base):
  __tablename__ = "messages"

  id = Column(Integer, primary_key=True, index=True)
  conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
  sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
  content = Column(Text, nullable=False)
  created_at = Column(DateTime, default=datetime.utcnow)

  # Relationships
  conversation = relationship("Conversation", back_populates="messages")
  # FIX: Change "User" to "UserModel"
  sender = relationship("UserModel", back_populates="messages")
  statuses = relationship(
      "MessageStatus", back_populates="message", cascade="all, delete-orphan"
  )


class MessageStatus(Base):
  __tablename__ = "message_status"

  id = Column(Integer, primary_key=True, index=True)
  message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
  user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
  is_delivered = Column(Boolean, default=False)
  is_read = Column(Boolean, default=False)

  # Relationships
  message = relationship("Message", back_populates="statuses")
  # FIX: Change "User" to "UserModel"
  user = relationship("UserModel", back_populates="message_statuses")