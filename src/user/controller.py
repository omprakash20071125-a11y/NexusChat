from fastapi import HTTPException, status, Request, BackgroundTasks,Depends
from src.user.dtos import UserCreate,LoginSchema
from sqlalchemy.orm import Session
from src.user.models import UserModel
from pwdlib import PasswordHash
from sqlalchemy import or_
import jwt
from src.utils.settings import settings
from datetime import datetime , timedelta
from jwt.exceptions import InvalidTokenError
from src.utils.mail import send_email

password_hash = PasswordHash.recommended()


# helper functions 
def get_password_hash(password):
    return password_hash.hash(password)

def verify_password(plain_password,hashed_password):
    return password_hash.verify(plain_password, hashed_password)


# registering user
async def register(body:UserCreate, db:Session,bg_task: BackgroundTasks):

    is_user = db.query(UserModel).filter(UserModel.username == body.username).first()
    if is_user:
        raise HTTPException(400, detail="Username already exist ..")

    is_user = db.query(UserModel).filter(UserModel.email == body.email).first()

    if is_user:
        raise HTTPException(400,detail = "email already exist ..")
    
    data = body.model_dump()

    hash_password = get_password_hash(body.password)

    user = UserModel(
        username = data["username"],
        hash_password = hash_password,
        email = data["email"]
        )
    db.add(user)
    db.commit()
    db.refresh(user)

    # bg_task.add_task(send_email, [user.email])
    
    return user

# login user
def login_user(body:LoginSchema,db:Session):
    data = db.query(UserModel).filter(UserModel.email == body.email).first()
    if not data:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED ,detail="wrong email")

    if not verify_password(body.password,data.hash_password):
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED ,detail="wrong password")

    exp_time = datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    token = jwt.encode({"_id":data.id,"exp":exp_time.timestamp()}, settings.SECRET_KEY, settings.ALGORITHM )

    return {"token": token}

# headers 
def is_authenticated(request: Request, db:Session):    
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

def search(query: str,main_user : UserModel,db:Session):
    users = (
      db.query(UserModel)
      .filter(
          or_(
              UserModel.username.ilike(f"%{query}%"),
              UserModel.email.ilike(f"%{query}%"),
          ),
          UserModel.id != main_user.id,
      )
      .all()
  )
    return users