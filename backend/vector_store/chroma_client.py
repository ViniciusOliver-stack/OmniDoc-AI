import os
import chromadb
from chromadb.config import Settings

# Definimos onde o banco vetorial vai salvar os dados fisicamente no seu PC
CHROMA_DB_DIR = os.path.join(os.getcwd(), "chroma_db")

# Garantindo que a pasta exista
os.makedirs(CHROMA_DB_DIR, exist_ok=True)

# Inicializamos o cliente do ChromaDB 
# O ChromaDB vai criar arquivos do SQLite otimizados para vetores nessa pasta
chroma_client = chromadb.PersistentClient(
    path=CHROMA_DB_DIR,
    settings=Settings(anonymized_telemetry=False)
)

# Criamos (ou pegamos, se já existir) uma "Collection" (O equivalente a uma Tabela no SQL)
# Usaremos essa collection para guardar todos os pedaços de texto (chunks)
document_collection = chroma_client.get_or_create_collection(name="omnidoc_collection")

def get_chroma_collection():
    """
    Função utilitária para importarmos a collection em outros arquivos
    de forma limpa e modular.
    """
    return document_collection


def delete_document_chunks(document_id: int):
    """
    Remove TODOS os chunks de um documento do ChromaDB.
    Deve ser chamado sempre que um documento for deletado do PostgreSQL
    para evitar chunks órfãos que poluem as buscas RAG.
    """
    collection = get_chroma_collection()
    # Busca todos os IDs de chunks que pertencem a esse document_id
    results = collection.get(where={"document_id": document_id})
    ids_to_delete = results.get("ids", [])
    if ids_to_delete:
        collection.delete(ids=ids_to_delete)
        print(f"[✓] ChromaDB: {len(ids_to_delete)} chunks do documento {document_id} removidos.")
    else:
        print(f"[!] ChromaDB: Nenhum chunk encontrado para o documento {document_id}.")