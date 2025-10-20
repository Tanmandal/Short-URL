from pydantic import BaseModel
from datetime import datetime
class URLEntry(BaseModel):
    url_code: str
    url_pass: str=""
    url: str

class URLStats(BaseModel):
    url_code: str
    url_hits: int
    url_created_at: datetime
    url_state: bool
    

class LoginEntry(BaseModel):
    url_code: str
    url_pass: str 

class ResetEntry(BaseModel):
    url_code: str
    old_url_pass: str 
    new_url_pass: str