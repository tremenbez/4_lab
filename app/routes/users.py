from fastapi import APIRouter, HTTPException
import redis
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import Depends
from http import HTTPStatus
from app.database import SessionLocal, engine, get_db
from app.routes.auth import get_current_user
from app.models.request_models import RegisterRequest, LoginRequest, RefreshTokenRequest, UpdateUserRequest
from app.models.mybaseclasses import Base, User, LoginHistory
from app.auth_functions import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)

redis_client = redis.Redis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), db=0)

router = APIRouter(prefix="/user", tags=["user"])
    
# Регистрация пользователя
@router.post("/register")
def register(user: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    new_user = User(email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    return {"message": "User registered successfully"}

# Аутентификация пользователя
@router.post("/login")
def login(user: LoginRequest, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid credentials")
    
    access_token = create_access_token({"sub": db_user.email})
    refresh_token = create_refresh_token({"sub": db_user.email})
    
    redis_client.setex(db_user.email, timedelta(days=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS"))), refresh_token)
    
    login_history = LoginHistory(user_id=db_user.id, user_agent="user_agent_placeholder", login_time=datetime.utcnow())
    db.add(login_history)
    db.commit()
    
    return {"access_token": access_token, "refresh_token": refresh_token}

# Обновление токена
@router.post("/refresh")
def refresh_token(request: RefreshTokenRequest):
    payload = decode_token(request.refresh_token)
    if not payload:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid refresh token")
    
    email = payload.get("sub")
    stored_refresh_token = redis_client.get(email)
    if not stored_refresh_token or stored_refresh_token.decode() != request.refresh_token:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid refresh token")
    
    new_access_token = create_access_token({"sub": email})
    return {"access_token": new_access_token}

# Изменение данных пользователя
@router.put("/user/update")
def update_user(
    user_data: UpdateUserRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user_data.email:
        current_user.email = user_data.email
    if user_data.password:
        current_user.hashed_password = get_password_hash(user_data.password)
    
    db.commit()
    return {"message": "User updated successfully"}

# Просмотр истории входов
@router.get("/user/history")
def get_login_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    history = db.query(LoginHistory).filter(LoginHistory.user_id == current_user.id).all()
    return [{"user_agent": entry.user_agent, "login_time": entry.login_time} for entry in history]

# Выход из системы
@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    redis_client.delete(current_user.email)
    return {"message": "Logged out successfully"}