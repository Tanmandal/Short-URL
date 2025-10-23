import os
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

SECRET_KEY= os.getenv("SECRET_KEY")
ALGORITHM= 'HS256'
TOKEN_EXPIRE=int(os.getenv("TOKEN_EXPIRE", "5"))

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def hash_password(password: str):
    if len(password)==0:
        return ""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password,hashed_password)

def create_access_token(data: dict,expire_delta: timedelta = None):
    to_encode=data.copy()
    expire = datetime.utcnow()+(expire_delta if expire_delta else timedelta(minutes=TOKEN_EXPIRE))
    to_encode.update({"exp":expire})
    encoded_jwt=jwt.encode(to_encode, SECRET_KEY,algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token:str):
    try:
        payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None