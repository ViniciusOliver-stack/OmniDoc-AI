from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.db.database import get_db
from backend.models.models import User

router = APIRouter()

class UserCreateRequest(BaseModel):
    name: str
    email: str

@router.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return user

@router.get("/users/")
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

@router.post("/users/")
def create_user(user_request: UserCreateRequest, db: Session = Depends(get_db)):
    exist_user = db.query(User).filter(User.name == user_request.name).first()
    if exist_user:
        raise HTTPException(status_code=400, detail="Usuário já existe.")
    
    new_user = User(name=user_request.name, email=user_request.email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user