from fastapi import FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError
from contextlib import asynccontextmanager
import os
import helper
from auth_utils import hash_password , create_access_token ,verify_password
from datetime import datetime

MONGO_URI = os.getenv("MONGO_URI")

class URLEntry(BaseModel):
    url_code: str
    url_pass: str
    url: str

class LoginEntry(BaseModel):
    url_code: str
    url_pass: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.mongodb_client = AsyncIOMotorClient(MONGO_URI)
    app.db = app.mongodb_client["ShortURL"]
    app.URLMap=app.db["URLMap"]
    await app.URLMap.create_index("url_code", unique=True)
    yield
    app.mongodb_client.close()

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def read_root():
    return {"message": "Welcome to URL Shortener"}

@app.post("/create", status_code=status.HTTP_201_CREATED)
async def create_url(entry: URLEntry):
    if not helper.validCode(entry.url_code):
        raise HTTPException(status_code=400, detail="Invalid URL code")
    entry.url=helper.formatURL(entry.url)
    entry.url_pass=hash_password(entry.url_pass)
    #entry.created_at=datetime.utcnow()
    try:
        await app.URLMap.insert_one(entry.model_dump())
        return {"message": "URL created", "data": entry.url}
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="URL code already exists")

@app.get("/{url_code:path}")
async def redirect_to_url(url_code: str):
    url_sub=''
    if '/' in url_code:
        index=url_code.find('/')
        url_sub=url_code[index:]
        url_code=url_code[:index]

    entry = await app.URLMap.find_one({"url_code": url_code})
    if entry:
        return RedirectResponse(url=entry["url"]+url_sub)
    raise HTTPException(status_code=404, detail="Short URL not found")

@app.post("/login")
async def login(login_entry:LoginEntry):
    entry = await app.URLMap.find_one({"url_code": login_entry.url_code})
    if entry and verify_password(login_entry.url_pass,entry.get("url_pass")):
        access_token = create_access_token(data={"url_code": entry["url_code"]})
        return {"access_token":access_token, "token_type":"bearer"}
    elif entry and len(entry.url_pass)==0:
        raise HTTPException(status_code=400, detail="Invalid request")
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")
