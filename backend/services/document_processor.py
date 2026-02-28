import os
import time
import tempfile
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from backend.vector_store.chroma_client import get_chroma_collection
from backend.services.s3_service import download_file_from_s3

embeddings_model = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")

# Limite conservador do tier gratuito: 100 req/min → processa em lotes de 20
BATCH_SIZE = 20


def _embed_with_retry(texts: list[str], max_retries: int = 5) -> list:
    """
    Gera embeddings com retry automático e backoff exponencial em caso de
    rate limit (429 RESOURCE_EXHAUSTED) da API do Gemini.
    """
    for attempt in range(max_retries):
        try:
            return embeddings_model.embed_documents(texts)
        except Exception as e:
            err = str(e)
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                # Extrai o tempo de espera sugerido pela API, se houver
                wait = 60 * (2 ** attempt)  # backoff: 60s, 120s, 240s...
                # Tenta pegar o retryDelay exato da mensagem
                import re
                match = re.search(r"retry in (\d+)", err, re.IGNORECASE)
                if match:
                    wait = int(match.group(1)) + 5  # +5s de margem
                print(f"  [Rate Limit] Aguardando {wait}s antes de tentar novamente (tentativa {attempt + 1}/{max_retries})...")
                time.sleep(wait)
            else:
                raise  # Outro tipo de erro — relança imediatamente
    raise RuntimeError(f"Falha ao gerar embeddings após {max_retries} tentativas.")


def process_and_store_pdf(
    file_path: str,
    document_id: int,
    scope: str,
    owner_user_id: int
):
    """
    Extrai o texto do PDF, fatia em chunks, gera embeddings com Gemini
    e salva no ChromaDB com metadados de escopo para o RAG multi-escopo.

    O arquivo é baixado do S3 para um arquivo temporário local,
    processado e depois removido automaticamente.

    Processa em lotes de BATCH_SIZE chunks para respeitar o rate limit
    da API do Gemini no tier gratuito (100 req/min).
    """
    # 1. Baixa o PDF do S3 para um arquivo temporário
    print(f"[S3] Baixando '{file_path}' para processamento...")
    pdf_bytes = download_file_from_s3(file_path)

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name

    try:
        # 2. Carrega o PDF do caminho temporário
        loader = PyPDFLoader(tmp_path)
        pages = loader.load()
    finally:
        os.remove(tmp_path)  # Garante limpeza mesmo se PyPDFLoader falhar

    # 3. Fatiamento em Chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_documents(pages)

    # 4. Preparar dados com metadados de escopo
    texts = []
    metadatas = []
    ids = []

    for i, chunk in enumerate(chunks):
        texts.append(chunk.page_content)
        metadatas.append({
            "document_id": document_id,
            "scope": scope,
            "owner_user_id": owner_user_id,
            "page": chunk.metadata.get("page", 0)
        })
        ids.append(f"doc_{document_id}_chunk_{i}")

    # 5. Gera embeddings em lotes + insere no ChromaDB lote a lote
    collection = get_chroma_collection()
    total = len(texts)

    print(f"[→] Documento {document_id} | {total} chunks | lotes de {BATCH_SIZE}")

    for start in range(0, total, BATCH_SIZE):
        end = min(start + BATCH_SIZE, total)
        batch_texts = texts[start:end]
        batch_metas = metadatas[start:end]
        batch_ids = ids[start:end]

        print(f"  Processando chunks {start + 1}–{end} de {total}...")
        batch_vectors = _embed_with_retry(batch_texts)

        collection.add(
            documents=batch_texts,
            embeddings=batch_vectors,
            metadatas=batch_metas,
            ids=batch_ids
        )

        # Pausa entre lotes para não pressionar o rate limit
        if end < total:
            time.sleep(2)

    print(f"[✓] Documento {document_id} (scope={scope}) | {total} chunks salvos no ChromaDB.")
