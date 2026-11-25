from app.core.security import hash_password, verify_password

password = "MySecretPassword123"

hashed = hash_password(password)

print("Generated hash:", hashed)
print("Correct password:", verify_password(password, hashed))
print("Incorrect password:", verify_password("WrongPassword", hashed))