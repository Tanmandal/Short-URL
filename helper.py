import re
def validCode(url_code: str) -> bool:
    key_words=['create','login','delete','pause','resume','details']
    if url_code in key_words:
        return False
    pattern = r'^[A-Za-z0-9_-]{3,20}$'
    return bool(re.match(pattern, url_code))

def formatURL(url: str):
    url=url.strip()
    if not url.startswith(("http://", "https://")):
        url="https://"+url
    return url
