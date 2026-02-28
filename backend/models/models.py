from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from backend.db.database import Base


# 1. Tabela de Usuários
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)

    # --- Autenticação ---
    # Nunca salvamos a senha em texto plano! Apenas o hash bcrypt.
    hashed_password = Column(String, nullable=True)  # nullable para não quebrar dados legados

    # --- Controle de Acesso (Role) ---
    # 'admin' → gerencia a base de documentos da empresa
    # 'user'  → faz perguntas e pode enviar documentos pessoais
    role = Column(String, default="user", nullable=False, server_default="user")

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relacionamentos
    documents = relationship("Document", back_populates="owner")
    chat_histories = relationship("ChatHistory", back_populates="user")


# 2. Tabela de Documentos (O PDF)
class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    file_path = Column(String)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    # --- Escopo do Documento ---
    # 'company' → documento da base da empresa (enviado por admin, visível a todos)
    # 'personal' → documento pessoal do usuário (visível só para ele)
    scope = Column(String, default="personal", nullable=False, server_default="personal")

    # Quem fez o upload
    user_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="documents")
    chat_histories = relationship("ChatHistory", back_populates="document")


# 3. Tabela de Histórico de Chat
class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    user_query = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user_id = Column(Integer, ForeignKey("users.id"))
    # nullable=True: conversa sem documento específico (RAG multi-escopo)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)

    user = relationship("User", back_populates="chat_histories")
    document = relationship("Document", back_populates="chat_histories")