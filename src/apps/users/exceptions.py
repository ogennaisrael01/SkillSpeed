import functools
import logging


logger = logging.getLogger(__name__)

def retry_on_failure(retry):
    def hold_func(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            for _ in range(retry):
                logger.info("Starting Task execution...")
                if attempt >= retry:
                    logger.error("max attempts exceeded. try again later")
                    raise ValueError("max attempts exceeded. try again later") 
                response = func(*args, **kwargs)
                if response:
                    return response
                attempt += 1
                logger.info("Retrying request...")
        return wrapper
    return hold_func


                
