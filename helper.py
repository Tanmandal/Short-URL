import re
def validCode(url_code: str) -> bool:
    key_words=['docs','redoc','create','login','delete','pause','resume','details','refresh_token','change_password','reset_hits','change_url','validate_token','health']
    if url_code.lower() in key_words:
        return False
    pattern = r'^[A-Za-z0-9_-]{3,20}$'
    return bool(re.match(pattern, url_code))

def formatURL(url: str):
    url=url.strip()
    if not url.startswith(("http://", "https://")):
        url="https://"+url
    return url

def listENV(env_str: str):
    env_list = env_str.split(",") if env_str else []
    return env_list

def validPass(url_pass:str):
    len_url_pass=len(url_pass)
    return len_url_pass==0 or (len_url_pass<=20 and len_url_pass>=3)

def blackURL(url:str,black_list: list):
    for black_list_url in black_list:
        if black_list_url in url:
            return True
    return False