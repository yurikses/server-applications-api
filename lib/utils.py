from itsdangerous import URLSafeSerializer

def generate_token(data: dict, secret: str):
    serializer = URLSafeSerializer(secret)
    token = serializer.dumps(data)
    return token    
    
def verify_token(token: str, secret: str) -> dict | None:
    serializer = URLSafeSerializer(secret)
    try:
        data = serializer.loads(token)
        return data
    except Exception:
        return None


def get_timestamp() -> int:
    import time
    return int(time.time())
    
    