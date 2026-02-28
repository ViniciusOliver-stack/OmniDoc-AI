from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from backend.vector_store.chroma_client import get_chroma_collection

embeddings_model = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")


def process_and_store_pdf(
    file_path: str,
    document_id: int,
    scope: str,
    owner_user_id: int
):
    """
    Extrai o texto do PDF, fatia em chunks, gera embeddings com Gemini
    e salva no ChromaDB com metadados de escopo para o RAG multi-escopo.

    Args:
        file_path: Caminho físico do arquivo PDF.
        document_id: ID do documento no PostgreSQL.
        scope: 'company' (base da empresa) ou 'personal' (documento do usuário).
        owner_user_id: ID do usuário que fez o upload.
    """
    # 1. Carrega o PDF
    loader = PyPDFLoader(file_path)
    pages = loader.load()

    # 2. Fatiamento em Chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_documents(pages)

    # 3. Preparar dados com metadados de escopo
    texts = []
    metadatas = []
    ids = []

    for i, chunk in enumerate(chunks):
        texts.append(chunk.page_content)
        metadatas.append({
            "document_id": document_id,
            "scope": scope,                  # 'company' ou 'personal'
            "owner_user_id": owner_user_id,  # ID de quem enviou
            "page": chunk.metadata.get("page", 0)
        })
        ids.append(f"doc_{document_id}_chunk_{i}")

    # 4. Gera embeddings e insere no ChromaDB
    embedded_vectors = embeddings_model.embed_documents(texts)

    collection = get_chroma_collection()
    collection.add(
        documents=texts,
        embeddings=embedded_vectors,
        metadatas=metadatas,
        ids=ids
    )

    print(f"[✓] Documento {document_id} (scope={scope}) | {len(chunks)} chunks salvos no ChromaDB.")