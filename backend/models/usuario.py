from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from backend.db.database import Base

class Usuario(Base):
    __tablename__ = "usuarios"  # Nome da tabela no PostgreSQL

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())