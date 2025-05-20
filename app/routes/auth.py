from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from app.models.mybaseclasses import User
from app.auth_functions import decode_token
from app.database import get_db
from http import HTTPStatus

def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid token")
    
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid token")
    
    email = payload.get("sub")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="User not found")
    
    return user