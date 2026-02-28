"""
Script de limpeza: remove do ChromaDB os chunks de documentos
que já foram deletados do PostgreSQL (chunks órfãos).

Execute: python cleanup_chroma.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from backend.db.database import SessionLocal
from backend.models.models import Document
from backend.vector_store.chroma_client import get_chroma_collection

db = SessionLocal()
collection = get_chroma_collection()

# 1. IDs de documentos que ainda existem no PostgreSQL
active_ids = {d.id for d in db.query(Document).all()}
print(f"Documentos ativos no PostgreSQL: {active_ids or 'nenhum'}")

# 2. Todos os chunks no ChromaDB
all_items = collection.get()
all_chunk_ids = all_items.get("ids", [])
all_metadatas = all_items.get("metadatas", [])

# 3. Identifica chunks cujo document_id não existe mais no PostgreSQL
orphan_ids = []
orphan_doc_ids = set()
for chunk_id, meta in zip(all_chunk_ids, all_metadatas):
    doc_id = meta.get("document_id")
    if doc_id not in active_ids:
        orphan_ids.append(chunk_id)
        orphan_doc_ids.add(doc_id)

if not orphan_ids:
    print("✅ Nenhum chunk órfão encontrado. ChromaDB está limpo!")
else:
    print(f"⚠️  Encontrados {len(orphan_ids)} chunks órfãos de {len(orphan_doc_ids)} documento(s): {orphan_doc_ids}")
    collection.delete(ids=orphan_ids)
    print(f"✅ {len(orphan_ids)} chunks removidos com sucesso!")

db.close()
