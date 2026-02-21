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
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relacionamentos (A "mágica" do SQLAlchemy)
    # Isso não cria uma coluna no banco, mas diz ao Python: "Um usuário tem vários documentos e históricos"
    documents = relationship("Document", back_populates="owner")
    chat_histories = relationship("ChatHistory", back_populates="user")


# 2. Tabela de Documentos (O PDF)
class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True) # Ex: "politica_rh.pdf"
    file_path = Column(String) # Onde o arquivo está salvo fisicamente (Ex: "/uploads/politica_rh.pdf")
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Chave Estrangeira (Foreign Key): É a ponte de ligação!
    # Dizemos ao banco: "Este documento PERTENCE ao usuário que tem este ID"
    user_id = Column(Integer, ForeignKey("users.id"))

    # Relacionamento de volta para o usuário
    owner = relationship("User", back_populates="documents")
    # Um documento pode ter várias conversas atreladas a ele
    chat_histories = relationship("ChatHistory", back_populates="document")


# 3. Tabela de Histórico de Chat
class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    user_query = Column(Text, nullable=False) # A pergunta do usuário (Text é melhor que String para textos longos)
    ai_response = Column(Text, nullable=False) # A resposta da IA
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # De quem é essa mensagem? (Chave Estrangeira para Users)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Sobre qual documento é essa mensagem? (Chave Estrangeira para Documents)
    # nullable=True significa que pode ser vazio (caso a pessoa faça uma pergunta geral pro sistema, sem ser de um PDF específico)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)

    # Relacionamentos
    user = relationship("User", back_populates="chat_histories")
    document = relationship("Document", back_populates="chat_histories")