from fastapi import FastAPI, Request
from src.realtime.socket_server import sio  # Import sio directly
from src.utils.db import Base, engine
import socketio  
from src.user.router import user_routes
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as redis
import os
from src.realtime.socket_server import socket_app
from src.chat.router import chat_routes
from src.realtime import events
load_dotenv()

Base.metadata.create_all(engine)


app = FastAPI(title = "Real time chat application")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(user_routes)
app.include_router(chat_routes)

@app.get("/")
def health():
    return "server is running fine"

app = socketio.ASGIApp(sio, app)