from pydantic import BaseModel

# Модели запросов
class RegisterRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class UpdateUserRequest(BaseModel):
    email: str = None
    password: str = None