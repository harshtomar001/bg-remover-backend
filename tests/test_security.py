from app.core.security import (
    create_access_token,
    decode_access_token
)

user_id = "550e8400-e29b-41d4-a716-446655440000"

# Create token
token = create_access_token(user_id)

print("Token generated:", bool(token))

# Decode token
payload = decode_access_token(token)

print("User ID:", payload["sub"])
print("Issued at:", payload["iat"])
print("Expires at:", payload["exp"])

import jwt

try:
    decode_access_token("invalid.token.value")
except jwt.InvalidTokenError:
    print("Invalid token correctly rejected.")