from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from backend.core.config import DATABASE_URL

engine = create_engine(DATABASE_URL) 
# Cada requisição vai usar uma sessão própria, garantindo que as operações sejam isoladas e seguras.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#Base que todos os meus Models vão herdar
Base = declarative_base()