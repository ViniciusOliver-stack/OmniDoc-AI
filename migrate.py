"""
Script de migração: adiciona as colunas novas sem apagar dados existentes.
Execute: python migrate.py
"""
import psycopg2
from backend.core.config import DATABASE_URL

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

print("Iniciando migração...")

# Tabela users: adiciona hashed_password e role
cur.execute("""
    ALTER TABLE users
    ADD COLUMN IF NOT EXISTS hashed_password VARCHAR,
    ADD COLUMN IF NOT EXISTS role VARCHAR NOT NULL DEFAULT 'user';
""")
print("  [OK] users.hashed_password e users.role adicionados.")

# Tabela documents: adiciona scope
cur.execute("""
    ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS scope VARCHAR NOT NULL DEFAULT 'personal';
""")
print("  [OK] documents.scope adicionado.")

conn.commit()
cur.close()
conn.close()

print("\nMigração concluída com sucesso! Reinicie o servidor.")
