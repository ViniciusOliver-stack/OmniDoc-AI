from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from backend.db.database import get_db
from backend.models.models import User
from backend.core.security import verify_password, get_password_hash, create_access_token
from backend.core.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Autenticação"])


# --- Schemas Pydantic ---

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    # Se não há nenhum admin no sistema, o primeiro usuário vira admin automaticamente.
    # Para criar admins depois, um admin existente deve alterar a role no banco.
    role: str = "user"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    name: str
    role: str


class UserMeResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str


# --- Endpoints ---

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Registra um novo usuário. 
    - Se não existe nenhum admin no sistema, o primeiro usuário cadastrado
      se torna admin automaticamente (independente do campo 'role').
    - Após o primeiro admin, todos os novos cadastros são 'user' por padrão.
    """
    # Checa email duplicado
    if db.query(User).filter(User.email == request.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este e-mail já está cadastrado."
        )

    # Lógica de role: primeiro usuário vira admin
    admin_exists = db.query(User).filter(User.role == "admin").first()
    role = "admin" if not admin_exists else "user"

    hashed_pw = get_password_hash(request.password)
    new_user = User(
        name=request.name,
        email=request.email,
        hashed_password=hashed_pw,
        role=role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": f"Usuário '{new_user.name}' criado com sucesso! Role: {new_user.role}",
        "user_id": new_user.id,
        "role": new_user.role
    }


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Autentica o usuário com email (campo 'username') e senha.
    Retorna um JWT Bearer token para uso nas demais requisições.
    """
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos."
        )

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos."
        )

    token = create_access_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        name=user.name,
        role=user.role
    )


@router.get("/me", response_model=UserMeResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Retorna os dados do usuário atualmente autenticado."""
    return UserMeResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role
    )
