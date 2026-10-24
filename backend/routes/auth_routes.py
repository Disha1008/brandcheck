from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from auth import verify_password, create_token, get_current_user
from database import get_db
from models import User
from schemas import LoginIn, TokenOut, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.lower().strip()).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Wrong email or password")
    return {"access_token": create_token(user), "token_type": "bearer", "user": user}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
