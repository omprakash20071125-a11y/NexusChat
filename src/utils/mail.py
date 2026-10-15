from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr, BaseModel
from typing import List

conf = ConnectionConfig(
    MAIL_USERNAME = "omgupta251107@gmail.com",
    MAIL_PASSWORD = "sclhbhbganuewyir",
    MAIL_FROM = "omgupta251107@gmail.com",
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_FROM_NAME="OM GUPTA",
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = False
)


async def send_email(email: List[str]):
    html = """<p>Hi Thanks For Registration. Our Team will connect with you soon</p> """

    message = MessageSchema(
        subject="Registration Confirmation",
        recipients=email,
        body=html,
        subtype=MessageType.html)

    fm = FastMail(conf)
    await fm.send_message(message)
    return {"message":"email has been sent"}