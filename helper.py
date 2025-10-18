import re
def validCode(url_code: str) -> bool:
    pattern = r'^[A-Za-z0-9_-]{3,20}$'
    return bool(re.match(pattern, url_code))