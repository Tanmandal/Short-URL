from fastapi import FastAPI, HTTPException, status, BackgroundTasks, Depends
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError
from contextlib import asynccontextmanager
from bson import ObjectId
import anyio
import os
import helper
from auth_utils import hash_password , create_access_token ,verify_password ,decode_access_token
from datetime import datetime
from models import *

MONGO_URI = os.getenv("MONGO_URI")
URL_BLACKLIST=helper.listENV(os.getenv("URL_BLACKLIST"))
SURL_BASE= os.getenv("SURL_BASE")

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.mongodb_client = AsyncIOMotorClient(MONGO_URI)
    app.db = app.mongodb_client["ShortURL"]
    app.URLMap=app.db["URLMap"]
    app.URLStats=app.db["URLStats"]
    await app.URLMap.create_index("url_code", unique=True)
    await app.URLStats.create_index("url_code", unique=True)
    yield
    app.mongodb_client.close()


security = HTTPBearer()
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=helper.listENV(os.getenv("ALLOWED_ORIGINS", "*")),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def delay(sec:int):
    import time
    start = time.time()
    while time.time() - start < sec:  # 30 seconds delay
        pass  # busy-wait, simulating congestion

def update_hits_sync(url_code: str):
    #delay(30)
    anyio.from_thread.run(app.URLStats.update_one, {"url_code": url_code}, {"$inc": {"url_hits": 1}})

async def get_url_code_by_id(id_str: str):
    try:
        obj_id = ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    entry = await app.URLMap.find_one({"_id": obj_id})
    if not entry:
        raise HTTPException(status_code=404, detail="Invalid or expired token")
    return entry.get("url_code")

async def authenticate(credentials:HTTPAuthorizationCredentials):
    if not credentials:
        raise HTTPException(status_code=status.HTTP_403_UNAUTHORIZED,details="Missing Credentials")
    token=credentials.credentials
    payload=decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Invalid or expired token")
    return await get_url_code_by_id(payload['url_id'])

@app.get("/")
async def read_root():
    return {"message": "Welcome to URL Shortener"}

@app.post("/create", status_code=status.HTTP_201_CREATED)
async def create_url(entry: URLEntry):
    if helper.blackURL(entry.url,URL_BLACKLIST):
        raise HTTPException(status_code=400, detail="URL Blacklisted")
    if not helper.validCode(entry.url_code):
        raise HTTPException(status_code=400, detail="Invalid URL code")
    if not helper.validPass(entry.url_pass):
        raise HTTPException(status_code=400, detail="Password length must be 3..20")
    entry.url=helper.formatURL(entry.url)
    entry.url_pass=hash_password(entry.url_pass)
    #entry.created_at=datetime.utcnow()
    try:
        await app.URLMap.insert_one(entry.model_dump())
        if len(entry.url)>0:
            await app.URLStats.insert_one({"url_code":entry.url_code,"url_hits":0,"url_created_at":datetime.utcnow(),"url_state":True})
        return {"message": "URL created", "short_url": SURL_BASE+"/"+entry.url_code}
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="URL code already exists")



@app.post("/login")
async def login(login_entry:LoginEntry):
    entry = await app.URLMap.find_one({"url_code": login_entry.url_code})
    if entry and len(entry['url_pass'])==0:
        raise HTTPException(status_code=400, detail="Invalid request")
    elif entry and verify_password(login_entry.url_pass,entry.get("url_pass")):
        access_token = create_access_token(data={"url_id": str(entry["_id"])})
        return {"access_token":access_token, "token_type":"bearer"}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
@app.post("/change_password")
async def change_password(reset_entry:ResetEntry,credentials:HTTPAuthorizationCredentials=Depends(security)):
    url_code=await authenticate(credentials)
    if url_code != reset_entry.url_code:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if reset_entry.old_url_pass==reset_entry.new_url_pass:
        raise HTTPException(status_code=400, detail="New password can't be same as old password")
    
    if not helper.validPass(reset_entry.new_url_pass):
        raise HTTPException(status_code=400, detail="Password length must be 3..20")
    
    entry = await app.URLMap.find_one({"url_code": url_code})
    if entry and verify_password(reset_entry.old_url_pass,entry.get("url_pass")):
        await app.URLMap.update_one({"url_code": url_code},{"$set": {"url_pass": hash_password(reset_entry.new_url_pass)}})
        return {"message": f"{url_code} password successfully changed"}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@app.delete("/delete")
async def delete(credentials:HTTPAuthorizationCredentials=Depends(security)):
    url_code=await authenticate(credentials)

    result_map = await app.URLMap.delete_one({"url_code": url_code})
    result_stats = await app.URLStats.delete_one({"url_code": url_code})

    if result_map.deleted_count == 0:
        raise HTTPException(status_code=404, detail="URL not found")
    else:
        return {"message": f"{url_code} successfully deleted"}
    
@app.patch("/pause")
async def pause(credentials:HTTPAuthorizationCredentials=Depends(security)):
    url_code=await authenticate(credentials)
    entry = await app.URLStats.find_one({"url_code": url_code})
    if entry:
        await app.URLStats.update_one({"url_code": url_code},{"$set": {"url_state": False}})
        return {"message": f"{url_code} successfully paused"}
    else:
        raise HTTPException(status_code=404, detail="URL not found")
    
@app.patch("/resume")
async def resume(credentials:HTTPAuthorizationCredentials=Depends(security)):
    url_code=await authenticate(credentials)
    entry = await app.URLStats.find_one({"url_code": url_code})
    if entry:
        await app.URLStats.update_one({"url_code": url_code},{"$set": {"url_state": True}})
        return {"message": f"{url_code} successfully resumed"}
    else:
        raise HTTPException(status_code=404, detail="URL not found")

@app.patch("/reset_hits")
async def reset_hits(credentials:HTTPAuthorizationCredentials=Depends(security)):
    url_code=await authenticate(credentials)
    entry = await app.URLStats.find_one({"url_code": url_code})
    if entry:
        await app.URLStats.update_one({"url_code": url_code},{"$set": {"url_hits": 0}})
        return {"message": f"{url_code} hits reset successfully"}
    else:
        raise HTTPException(status_code=404, detail="URL not found")

@app.patch("/change_url")
async def change_url(url:str,credentials:HTTPAuthorizationCredentials=Depends(security)):
    url_code=await authenticate(credentials)
    entry = await app.URLMap.find_one({"url_code": url_code})
    if entry:
        if helper.blackURL(url,URL_BLACKLIST):
            raise HTTPException(status_code=400, detail="URL Blacklisted")
        await app.URLMap.update_one({"url_code": url_code},{"$set": {"url": helper.formatURL(url)}})
        return {"message": f"{url_code} redirect url changed successfully"}
    else:
        raise HTTPException(status_code=404, detail="URL not found")
    
@app.get("/details")
async def details(credentials:HTTPAuthorizationCredentials=Depends(security)):
    url_code=await authenticate(credentials)
    entry1 = await app.URLStats.find_one({"url_code": url_code})
    if entry1:
        entry2 = await app.URLMap.find_one({"url_code": url_code})
        info=dict(entry1)
        info["url"]=entry2["url"]
        info.pop("_id", None)
        return {"message": "Details fetched successfully", "data": info}
    else:
        raise HTTPException(status_code=404, detail="URL not found")
    
@app.get("/validate_token")
async def validate_token(credentials:HTTPAuthorizationCredentials=Depends(security)):
    url_code=await authenticate(credentials)
    entry1 = await app.URLStats.find_one({"url_code": url_code})
    if entry1:
        return {"message": "Access token is Valid"}
    else:
        raise HTTPException(status_code=404, detail="Access token not Valid")
    

@app.get("/refresh_token")
async def refresh_token(credentials:HTTPAuthorizationCredentials=Depends(security)):
    url_code=await authenticate(credentials)
    entry = await app.URLMap.find_one({"url_code": url_code})
    if entry and len(entry.get("url_pass"))>0:
        access_token = create_access_token(data={"url_id": str(entry["_id"])})
        return {"access_token":access_token, "token_type":"bearer"}
    else:
        raise HTTPException(status_code=404, detail="Invalid or expired token")


@app.get("/health")
async def health_check():
    try:
        await app.db.command("ping")
        return {"message": "Database is active"}
    except Exception as e:
        raise HTTPException(status_code=404,detail= f"Database connection failed: {str(e)}")

@app.get("/{url_code:path}")
async def redirect_to_url(url_code: str,background_tasks: BackgroundTasks):
    url_sub=''
    if '/' in url_code:
        index=url_code.find('/')
        url_sub=url_code[index:]
        url_code=url_code[:index]

    entry = await app.URLMap.find_one({"url_code": url_code})
    if entry:
        if len(entry["url_pass"])>0:
            stats = await app.URLStats.find_one({"url_code": url_code})
            if not stats["url_state"]:
                raise HTTPException(status_code=423, detail="Redirect temporarily paused")
            else:
               background_tasks.add_task(update_hits_sync, url_code)
        return RedirectResponse(url=entry["url"]+url_sub)
    raise HTTPException(status_code=404, detail="Short URL not found")