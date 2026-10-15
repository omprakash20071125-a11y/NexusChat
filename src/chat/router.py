from fastapi import APIRouter, Depends, Request, status, BackgroundTasks
from typing import List
from src.chat import controller
from src.user.models import UserModel
from src.utils.db import get_db
from src.utils.helpers import is_authenticated
from sqlalchemy.orm import Session
from src.chat.dtos import ConversationCreateDTO, MessageCreateDTO, ConversationUpdateDTO


chat_routes = APIRouter(prefix = "/chat")

@chat_routes.post("/conversations")
def conversation(dto: ConversationCreateDTO,user_data: UserModel = Depends(is_authenticated),db:Session=Depends(get_db)):
    return controller.create_conversation(
      db=db, current_user_id=user_data.id, dto=dto
  )

@chat_routes.get("/conversations") # all chats user currently logged in 
def all_conversation(user_data: UserModel = Depends(is_authenticated),db:Session=Depends(get_db)):
    return controller.get_user_conversations(user_data.id,db)

@chat_routes.get("/conversations/{conversation_id}/messages")
def conversation_messages(conversation_id:int,user_data: UserModel = Depends(is_authenticated),db:Session=Depends(get_db)):
    return controller.conversation_messages(conversation_id,user_data,db)

@chat_routes.post("/conversations/{conversation_id}/participants")
def add_new_member(new_user_id:int,conversation_id:int,db:Session=Depends(get_db),user_data: UserModel = Depends(is_authenticated)):
    return controller.add_new_member(new_user_id,conversation_id,user_data,db)


@chat_routes.post("/conversations/{conversation_id}/messages")
def add_new_message(conversation_id:int,message:MessageCreateDTO,user:UserModel=Depends(is_authenticated),db:Session=Depends(get_db)):
    return controller.add_new_message(conversation_id,message,user,db)

# @chat_routes.get("/conversations/{conversation_id}")
# def get_single_conversation(
#     conversation_id: int,
#     user_data: UserModel = Depends(is_authenticated),
#     db: Session = Depends(get_db),
# ):
#   return controller.get_conversation_details(conversation_id, user_data, db)

@chat_routes.delete("/conversations/{conversation_id}/leave")
def leave_room_yourself(conversation_id:int,user_data:UserModel = Depends(is_authenticated),db:Session=Depends(get_db)):
    return controller.leave_room_yourself(conversation_id,user_data,db)

@chat_routes.delete("/conversations/{conversation_id}/participants/{target_user_id}")
def  delete_by_admin(conversation_id:int,target_user_id: int,user_data:UserModel = Depends(is_authenticated),db:Session=Depends(get_db)):
    return controller.delete_by_admin(conversation_id,target_user_id,user_data,db)

@chat_routes.patch("/conversations/{conversation_id}")
def update_group_details(
    conversation_id: int,
    dto: ConversationUpdateDTO,
    user_data: UserModel = Depends(is_authenticated),
    db: Session = Depends(get_db),
):
  return controller.update_conversation(conversation_id, dto, user_data, db)

@chat_routes.post("/conversations/{conversation_id}/read")
def mark_conversation_as_read(
    conversation_id: int,
    user_data: UserModel = Depends(is_authenticated),
    db: Session = Depends(get_db),
):
  return controller.mark_messages_as_read(conversation_id, user_data, db)

@chat_routes.get("/conversations/{conversation_id}/search")
def search_conversation_messages(
    conversation_id: int,
    query: str,
    user_data: UserModel = Depends(is_authenticated),
    db: Session = Depends(get_db),
):
  return controller.search_messages(conversation_id, query, user_data, db)

@chat_routes.get("/conversations/{conversation_id}")
def get_conversation_details_endpoint(
    conversation_id: int,
    db=Depends(get_db),
    current_user: UserModel = Depends(is_authenticated),
):
  return controller.get_conversation_participants_logic(
      conversation_id=conversation_id,
      current_user_id=current_user.id,
      db=db,
  )