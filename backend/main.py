from fastapi import FastAPI
from backend.db.database import engine, Base
from  backend.api import documents, user

# Importar os Models para que o SQLAlchemy os "Conheça"
from backend.models.models import User, Document, ChatHistory

app = FastAPI()

# Cria as tabelas no banco automaticamente ao iniciar a aplicação
# Se a tabela já existe, ele não recria (não apaga seus dados)
Base.metadata.create_all(bind=engine)
  
app.include_router(documents.router) # Adiciona as rotas de documentos à aplicação 
app.include_router(user.router)      # Adiciona as rotas de usuário à aplicação
    
@app.get("/")
def raiz():
    return {"mensagem": "API funcionando!"}