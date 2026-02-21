from fastapi import FastAPI
from backend.db.database import engine, Base
from backend.api import usuarios

# Importar os Models para que o SQLAlchemy os "Conheça"
from backend.models import usuario
from backend.models.models import User, Document, ChatHistory

app = FastAPI()

# Cria as tabelas no banco automaticamente ao iniciar a aplicação
# Se a tabela já existe, ele não recria (não apaga seus dados)
Base.metadata.create_all(bind=engine)
  
app.include_router(usuarios.router) # Adiciona as rotas de usuários à aplicação  
    
@app.get("/")
def raiz():
    return {"mensagem": "API funcionando!"}