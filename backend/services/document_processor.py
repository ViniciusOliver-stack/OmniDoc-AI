from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# importamos a collection do ChromaDB para guardar os chunks depois de processados
from backend.vector_store.chroma_client import get_chroma_collection

# O LangChain vai puxar a GOOGLE_API_KEY do arquivo .env automaticamente
embeddings_model = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")

def process_and_store_pdf(file_path: str, document_id: int):
    """
    Extrai o texto, fatia, gera embeddings com Gemini e salva no ChromaDB.
    """
    # 1. Carrega o texto PDF
    loader = PyPDFLoader(file_path)
    pages = loader.load()
    
    # 2. Fatiamento em Chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_documents(pages)
    
    # 3. Preparar os dados para o ChromaDB
    texts = []
    metadatas = []
    ids = []
    
    for i, chunk in enumerate(chunks):
        texts.append(chunk.page_content)
        
        # Guardaremos o document_id dentro do vetor para que a IA não misture contratos do Usuário A com os do Usuário B
        metadatas.append({
            "document_id": document_id,
            "page": chunk.metadata.get("page", 0)
        })
        
        # Cada chunk precisa ter um ID único no banco vetorial
        ids.append(f"doc_{document_id}_chunk_{i}")
        
    # 4. Gerar Embeddings e Inserir o valor no Banco Vetorial (ChromaDB)
    # O método embed_documents envia os textos para a API do Gemini e recebe os números de volta
    embedded_vectors = embeddings_model.embed_documents(texts)
    
    collection = get_chroma_collection()
    
    # Inserir os dados no ChromaDB
    collection.add(
        documents=texts,
        embeddings=embedded_vectors,
        metadatas=metadatas,
        ids=ids
    )
    
    print(f"Documento {document_id} processado! {len(chunks)} chunks salvos no ChromaDB.")