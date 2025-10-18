from fastapi import FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError
from contextlib import asynccontextmanager
import os
import helper

MONGO_URI = os.getenv("MONGO_URI")

class URLEntry(BaseModel):
    url_code: str
    url: str

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
    if helper.validCode(entry.url_code):
        raise HTTPException(status_code=400, detail="Invalid URL code")
    entry.url=helper.formatURL(entry.url)
    try:
        await app.URLMap.insert_one(entry.model_dump())
        return {"message": "URL created", "data": entry.model_dump()}
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
