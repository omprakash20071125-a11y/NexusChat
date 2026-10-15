import jwt
from fastapi import HTTPException
from src.chat import controller
from src.chat.dtos import MessageCreateDTO
from src.realtime.socket_server import sio
from src.user.models import UserModel
from src.utils.db import SessionLocal  # Import your database session maker
from src.utils.settings import settings



@sio.event
async def connect(sid, environ, auth):
  """Triggers when a client opens a live WebSocket connection.

  Expects the frontend to pass the JWT token in the connection auth dictionary:
  io({ auth: { token: "your_jwt_token" } })
  """
  print("--- SOCKET CONNECT ATTEMPT ---")
  print("Received auth:", auth)  # See if the token is arriving
  if not auth or "token" not in auth:
    print(f"Connection rejected for {sid}: No token provided")
    return False  # Reject connection

  token = auth["token"]

  try:
    # Decode the token using your app's secret key and algorithm
    payload = jwt.decode(
        token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )
    user_id: int = payload.get("_id")  # Or whatever key holds your user id
    if user_id is None:
      return False

    # Open a manual database session to fetch the user
    db = SessionLocal()
    try:
      user = db.query(UserModel).filter(UserModel.id == user_id).first()
      if not user:
        return False

      # Store user data securely in the socket's session storage
      await sio.save_session(sid, {"user_id": user.id, "email": user.email})
      print(f"User {user.id} connected successfully with socket ID {sid}")
    finally:
      db.close()

  except jwt.PyJWTError:
    print(f"Connection rejected for {sid}: Invalid token")
    return False


@sio.event
async def disconnect(sid):
  """Triggers automatically when a client closes their app or loses connection."""
  print(f"Socket disconnected: {sid}")


@sio.on("join_room")
async def join_room(sid, data):
  """Listens when a user clicks into a conversation room on their frontend.

  Expected payload from client: { "conversation_id": 5 }
  """
  conversation_id = data.get("conversation_id")
  if not conversation_id:
    return {"error": "conversation_id is required"}

  # Convert conversation_id to a string room name
  room_name = str(conversation_id)

  # Add this socket connection to the specific Socket.IO room
  await sio.enter_room(sid, room_name)
  print(f"Socket {sid} joined conversation room: {room_name}")

  return {"status": "success", "room": room_name}

@sio.on("send_message")
async def handle_send_message(sid, data):
  """Catches incoming live messages sent over the socket, saves them to PostgreSQL via

  your controller, and broadcasts them instantly to everyone in the room.

  Expected payload from client: { "conversation_id": 5, "content": "Hello world!"
  }
  """
  conversation_id = data.get("conversation_id")
  content = data.get("content")

  if not conversation_id or not content:
    return {"error": "conversation_id and content are required"}

  # Retrieve the logged-in user's ID stored during the connection handshake
  session = await sio.get_session(sid)
  user_id = session.get("user_id")

  if not user_id:
    return {"error": "Unauthorized"}

  # Open a manual database session to execute your controller logic
  db = SessionLocal()
  try:
    # Fetch the user model object for the controller security check
    user_data = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user_data:
      return {"error": "User not found"}

    # Wrap the string content into your MessageCreateDTO
    dto = MessageCreateDTO(content=content)

    # 1. Reuse your exact existing controller function!
    # This securely validates membership, creates the message, and commits to PostgreSQL.
    saved_message = controller.add_new_message(
        conversation_id=conversation_id, message=dto, user=user_data, db=db
    )

    # Prepare message data to broadcast (convert fields to a dictionary/json-safe format)
    message_payload = {
        "id": saved_message.id,
        "conversation_id": saved_message.conversation_id,
        "sender_id": saved_message.sender_id,
        "content": saved_message.content,
        "created_at": str(saved_message.created_at),
    }

    # 2. Broadcast the message instantly to EVERY socket inside this conversation room
    room_name = str(conversation_id)
    await sio.emit("new_message", message_payload, room=room_name)

    print(
        f"Message broadcasted to room {room_name} from user {user_id}:"
        f" {content}"
    )
    return {"status": "sent", "message": message_payload}

  except HTTPException as e:
    # Catch your controller's explicit HTTP exceptions (like 403 or 404) and return them to the client
    return {"error": e.detail, "status_code": e.status_code}
  except Exception as e:
    print(f"Error sending message: {e}")
    return {"error": "Internal server error"}
  finally:
    db.close()