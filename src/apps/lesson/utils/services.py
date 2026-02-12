import re

def validate_urls(urls: str) -> bool:
    valid_url_format = r'^(https?|ftp)://[^\s/$.?#].[^\s]*$'

    if not re.match(valid_url_format, urls):
        return False
    return True