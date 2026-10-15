from fastapi import APIRouter, Depends, Request, status, BackgroundTasks
from typing import List
from src.user import controller
from src.user.models import UserModel
from src.user.dtos import UserCreate, UserResponseSchema, LoginSchema
from src.utils.db import get_db
from src.utils.helpers import is_authenticated
from sqlalchemy.orm import Session

user_routes = APIRouter(prefix="/user")

@user_routes.post("/register",response_model=UserResponseSchema,status_code=status.HTTP_201_CREATED)
async def register(body:UserCreate,bg_task:BackgroundTasks,db:Session = Depends(get_db)):
    return await controller.register(body,db,bg_task)

@user_routes.post("/login",status_code=status.HTTP_200_OK)
async def login(body:LoginSchema,db:Session = Depends(get_db)):
    return controller.login_user(body,db) 

@user_routes.get("/is_auth",response_model=UserResponseSchema,status_code=status.HTTP_200_OK)
async def is_auth(request:Request,db:Session = Depends(get_db)):
    return controller.is_authenticated(request,db)

@user_routes.get("/me",response_model=UserResponseSchema)
async def get_my_profile(current_user:UserModel= Depends(is_authenticated),db:Session = Depends(get_db)):
    return current_user

@user_routes.get("/search",response_model=List[UserResponseSchema])
async def search(query: str,main_user : UserModel = Depends(is_authenticated),db:Session = Depends(get_db)):
    return controller.search(query,main_user,db)