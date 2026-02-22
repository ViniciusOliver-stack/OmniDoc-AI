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