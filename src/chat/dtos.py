from typing import List, Optional
from pydantic import BaseModel


class ConversationCreateDTO(BaseModel):
  participant_ids: List[int]
  is_group: bool = False
  name: Optional[str] = None

class MessageCreateDTO(BaseModel):
  content: str

class ConversationUpdateDTO(BaseModel):
  name: Optional[str] = None