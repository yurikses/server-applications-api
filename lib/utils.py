from passlib.context import CryptContext

def get_timestamp() -> int:
    import time
    return int(time.time())
    
appctx = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  
)

def hash_password(password: str) -> str:
    return appctx.hash(password)
    
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return appctx.verify(plain_password, hashed_password)

