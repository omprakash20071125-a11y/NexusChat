from fastapi import Request,HTTPException, status, Depends
import jwt
from src.utils.db import get_db
from sqlalchemy.orm import Session
from src.utils.settings import settings
from datetime import datetime , timedelta
from jwt.exceptions import InvalidTokenError
from src.user.models import UserModel
import random


def is_authenticated(request: Request, db:Session = Depends(get_db)):    
    try:
        token = request.headers.get("authorization")
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="you are unauthorized")
        token = token.split(" ")[-1]
        data = jwt.decode(token,settings.SECRET_KEY,settings.ALGORITHM) # user data(payload)
        user_id = data.get("_id")
        
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="you are unauthorized")
        
        return user
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="you are unauthorized")

def get_ttl_with_jitter(base_ttl: int = 300, jitter: int = 60) -> int:
    return base_ttl + random.randint(-jitter, jitter)