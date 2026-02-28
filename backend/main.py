from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.db.database import engine, Base
from backend.api import documents, user, chat, auth

from backend.models.models import User, Document, ChatHistory

app = FastAPI(
    title="OmniDoc AI",
    description="Assistente de documentos corporativos com RAG multi-escopo.",
    version="2.0.0"
)

# CORS para o frontend Streamlit se comunicar com o backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cria as tabelas automaticamente (não recria se já existem)
Base.metadata.create_all(bind=engine)

# Registra os routers
app.include_router(auth.router)        # /auth/login, /auth/register, /auth/me
app.include_router(documents.router)   # /documents/upload/company, /documents/upload/personal
app.include_router(user.router)        # /users/
app.include_router(chat.router)        # /chat/


@app.get("/", tags=["Health"])
def raiz():
    return {"status": "ok", "message": "OmniDoc AI v2.0 rodando!"}