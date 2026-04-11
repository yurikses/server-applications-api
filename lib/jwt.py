import jwt

def create_jwt_token(data: dict, secret_key: str, algorithm: str = "HS256") -> str:
    return jwt.encode(data, secret_key, algorithm=algorithm)
    
def decode_jwt_token(token: str, secret_key: str, algorithms: list[str] = ["HS256"]) -> dict:
    try:
        return jwt.decode(token, secret_key, algorithms=algorithms)
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")