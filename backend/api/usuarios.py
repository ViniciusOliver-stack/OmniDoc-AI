from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.db.database import SessionLocal
from backend.models.usuario import Usuario

router = APIRouter()

# Esse é o "gerente de sessão" — abre e fecha a sessão automaticamente
def get_db():
    db = SessionLocal()  # Abre a sessão
    try:
        yield db          # Entrega a sessão para o endpoint usar
    finally:
        db.close()        # Sempre fecha, mesmo se der erro

# Pydantic valida o que chega no corpo da requisição
class UsuarioCreate(BaseModel):
    nome: str
    email: str

# GET — Buscar todos os usuários
@router.get("/usuarios")
def listar_usuarios(db: Session = Depends(get_db)):
    usuarios = db.query(Usuario).all()
    return usuarios

# POST — Criar um novo usuário
@router.post("/usuarios")
def criar_usuario(dados: UsuarioCreate, db: Session = Depends(get_db)):
    # Verifica se o email já existe
    existente = db.query(Usuario).filter(Usuario.email == dados.email).first()
    if existente:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    novo_usuario = Usuario(nome=dados.nome, email=dados.email)
    db.add(novo_usuario)      # "Anota" a intenção de inserir
    db.commit()               # Executa de verdade no banco
    db.refresh(novo_usuario)  # Atualiza o objeto com os dados do banco (ex: id gerado)
    return novo_usuario