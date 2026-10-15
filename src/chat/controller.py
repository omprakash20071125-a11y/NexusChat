from fastapi import HTTPException, status, Request, BackgroundTasks,Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_
import jwt
from src.user.models import UserModel
from src.utils.settings import settings
from datetime import datetime , timedelta
from jwt.exceptions import InvalidTokenError
from src.chat.dtos import ConversationCreateDTO, MessageCreateDTO, ConversationUpdateDTO
from src.chat.models import Conversation, ConversationParticipant, Message

def create_conversation(db: Session, current_user_id:int , dto: ConversationCreateDTO):
    db_conversation = Conversation(
      is_group=dto.is_group, name=dto.name if dto.is_group else None
    )
    db.add(db_conversation)
    db.flush()  # Flushes to generate db_conversation.id before committing

    # Step 2: Combine the creator with the requested participant IDs (avoiding duplicates)
    all_participants = set(dto.participant_ids)
    all_participants.add(current_user_id)

    # Step 3: Insert rows into the junction table for each participant
    for user_id in all_participants:
        participant = ConversationParticipant(
            user_id=user_id, conversation_id=db_conversation.id
        )
        db.add(participant)

    # Step 4: Commit transaction and refresh object
    db.commit()
    db.refresh(db_conversation)

    return db_conversation

def get_user_conversations(user_id:int,db:Session):
    participant_records = (
      db.query(ConversationParticipant)
      .filter(ConversationParticipant.user_id == user_id)
      .all()
    )
    conversations = [p.conversation for p in participant_records]
    return conversations

def conversation_messages(conversation_id:int,user_data:UserModel,db:Session):
    data = db.query(Conversation).filter(Conversation.id == conversation_id).first()

    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail = "conversation don't exist")

    participant_user_ids = [p.user_id for p in data.participants]
    if user_data.id not in participant_user_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant in this conversation",
        )
    messages = data.messages
    return messages
    
def add_new_member(new_user_id:int,conversation_id:int,user_data:UserModel,db:Session):
    data = (
      db.query(Conversation)
      .filter(Conversation.id == conversation_id)
      .first()
    )
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
    )
    if not data.is_group:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add participants to a direct message",
    )

    participants_user_ids = [p.user_id for p in data.participants]

    if user_data.id not in participants_user_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant in this conversation",
    )
    if new_user_id in participants_user_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists in the conversation",
    )
    user = ConversationParticipant(user_id=new_user_id,conversation_id=conversation_id)

    db.add(user)
    db.commit()

    return {"message": "Participant added successfully"}

def add_new_message(conversation_id: int,message: MessageCreateDTO,user: UserModel,db: Session):
    data = (
          db.query(Conversation)
          .filter(Conversation.id == conversation_id)
          .first()
        )

    if not data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail = "conversation don't exist")

    participants_user_ids = [p.user_id for p in data.participants]

    if user.id not in participants_user_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a participant in this conversation",
        )

    new_message = Message(
      conversation_id=conversation_id,
      sender_id=user.id,
      content=message.content,  # <--- Here is where your string goes!
    )

    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    return new_message

def get_conversation_details(
    conversation_id: int, user_data: UserModel, db: Session
):
#   # Step 1: Find the conversation by its ID
#   data = (
#       db.query(Conversation)
#       .filter(Conversation.id == conversation_id)
#       .first()
#   )

#   if not data:
#     raise HTTPException(
#         status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
#     )

#   # Step 2: Security check - Verify the user is a participant of this chat
#   participant_user_ids = [p.user_id for p in data.participants]
#   if user_data.id not in participant_user_ids:
#     raise HTTPException(
#         status_code=status.HTTP_403_FORBIDDEN,
#         detail="You are not a participant in this conversation",
#     )

#   # Step 3: Return the conversation details
#   return data
    participant_records = (
        db.query(ConversationParticipant)
        .filter(ConversationParticipant.user_id == user_data.id)
        .all()
    )
    conversations = [p.conversation for p in participant_records]

    # Load every needed user in one query instead of one per participant
    all_user_ids = {p.user_id for c in conversations for p in c.participants}
    users = db.query(UserModel).filter(UserModel.id.in_(all_user_ids)).all() if all_user_ids else []
    users_by_id = {u.id: u for u in users}

    result = []
    for c in conversations:
        result.append({
            "id": c.id,
            "name": c.name,
            "is_group": c.is_group,
            "participants": [
                {
                    "id": users_by_id[p.user_id].id,
                    "username": users_by_id[p.user_id].username,
                    "email": users_by_id[p.user_id].email,
                }
                for p in c.participants
                if p.user_id in users_by_id
            ],
        })
    return result

def leave_room_yourself(conversation_id,user_data,db):
    data = (
          db.query(Conversation)
          .filter(Conversation.id == conversation_id)
          .first()
      )
    
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )
    participant_user_ids = [p.user_id for p in data.participants]
    if user_data.id not in participant_user_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant in this conversation",
        )
    participant_record = (
      db.query(ConversationParticipant)
      .filter(
          ConversationParticipant.conversation_id == conversation_id,
          ConversationParticipant.user_id == user_data.id,
      )
      .first()
  )

    if participant_record:
        db.delete(participant_record)
        db.commit()

    return {"message":"user deleted successfully for this conversation"}

def delete_by_admin(conversation_id: int,
    target_user_id: int,
    user_data: UserModel,
    db: Session):
    data = (
              db.query(Conversation)
              .filter(Conversation.id == conversation_id)
              .first()
          )
        
    if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
            )
    if not data.is_group:
        raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,detail="can't do that"
                    )
    participant_user_ids = [p.user_id for p in data.participants]
    if user_data.id not in participant_user_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a participant in this conversation",
            )
    if target_user_id not in participant_user_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user is not a participant in this conversation",
    )
    target_record = (
      db.query(ConversationParticipant)
      .filter(
          ConversationParticipant.conversation_id == conversation_id,
          ConversationParticipant.user_id == target_user_id,
      )
      .first()
  )
    if target_record:
        db.delete(target_record)
        db.commit()
    return {"message": "Participant removed successfully"}

def update_conversation(conversation_id:int, dto:ConversationUpdateDTO, user_data:UserModel, db:Session):
    data = (
      db.query(Conversation)
      .filter(Conversation.id == conversation_id)
      .first()
    )
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
    )

    if not data.is_group:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update details of a direct message",
    )
    participant_user_ids = [p.user_id for p in data.participants]
    if user_data.id not in participant_user_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant in this conversation",
    )

    if dto.name is not None:
        data.name = dto.name

    db.commit()
    db.refresh(data)

    return data

def mark_messages_as_read(
    conversation_id: int, user_data: UserModel, db: Session
):
  # 1. Check if the conversation exists
  data = (
      db.query(Conversation)
      .filter(Conversation.id == conversation_id)
      .first()
  )
  if not data:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
    )

  # 2. Verify the user is a participant of this conversation
  participant_user_ids = [p.user_id for p in data.participants]
  if user_data.id not in participant_user_ids:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not a participant in this conversation",
    )

  # 3. Use user_data.message_statuses to find and update unread statuses for this room
  for status_record in user_data.message_statuses:
    # Ensure it belongs to this conversation and is currently unread
    if (
        status_record.message
        and status_record.message.conversation_id == conversation_id
        and not status_record.is_read
    ):
      status_record.is_read = True

  db.commit()

  return {"message": "Messages marked as read successfully"}

def search_messages(
    conversation_id: int, query: str, user_data: UserModel, db: Session
):
  # 1. Check if the conversation exists
  data = (
      db.query(Conversation)
      .filter(Conversation.id == conversation_id)
      .first()
  )
  if not data:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
    )

  # 2. Verify the user is a participant of this conversation
  participant_user_ids = [p.user_id for p in data.participants]
  if user_data.id not in participant_user_ids:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not a participant in this conversation",
    )

  # 3. Search messages inside this conversation containing the keyword (case-insensitive)
  search_pattern = f"%{query}%"
  matching_messages = (
      db.query(Message)
      .filter(
          Message.conversation_id == conversation_id,
          Message.content.ilike(search_pattern),
      )
      .all()
  )

  return matching_messages

def get_conversation_participants_logic(
    conversation_id: int, current_user_id: int, db: Session
):
  # 1. Verify user membership in the conversation
  participant = db.query(ConversationParticipant).filter_by(
      conversation_id=conversation_id, user_id=current_user_id
  ).first()

  if not participant:
    raise HTTPException(status_code=403, detail="Not a member of this channel")

  # 2. Fetch conversation details
  conv = db.query(Conversation).filter_by(id=conversation_id).first()
  if not conv:
    raise HTTPException(status_code=404, detail="Conversation not found")

  # 3. Format participants list
  participants_list = []
  for p in conv.participants:
    user = db.query(UserModel).filter_by(id=p.user_id).first()
    if user:
      participants_list.append({
          "id": user.id,
          "username": user.username,
          "email": user.email,
      })

  return {
      "id": conv.id,
      "name": conv.name,
      "is_group": conv.is_group,
      "participants": participants_list,
  }