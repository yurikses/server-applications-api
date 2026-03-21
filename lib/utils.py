from itsdangerous import URLSafeSerializer

def generate_token(data: dict, secret: str):
    serializer = URLSafeSerializer(secret)
    token = serializer.dumps(data)
    return token    