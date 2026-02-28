from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from backend.vector_store.chroma_client import get_chroma_collection

embedding_model = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)


def generate_answer(user_query: str, user_id: int) -> str:
    """
    Busca contexto no banco vetorial com filtro MULTI-ESCOPO e gera a resposta.

    Estratégia de busca:
    - Documentos da empresa (scope='company'): acessíveis por todos.
    - Documentos pessoais (scope='personal', user_id=<user_id>): apenas do usuário.

    O usuário não precisa selecionar nenhum documento — a IA busca em tudo
    que é relevante automaticamente.
    """
    collection = get_chroma_collection()

    # Converte a pergunta em vetor de embedding para a busca semântica
    query_embedding = embedding_model.embed_query(user_query)

    # --- Busca 1: Documentos da base da empresa ---
    company_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=4,
        where={"scope": {"$eq": "company"}}
    )

    # --- Busca 2: Documentos pessoais do usuário ---
    personal_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3,
        where={
            "$and": [
                {"scope": {"$eq": "personal"}},
                {"owner_user_id": {"$eq": user_id}}
            ]
        }
    )

    # Consolidar todos os chunks encontrados
    company_chunks = company_results["documents"][0] if company_results["documents"] else []
    personal_chunks = personal_results["documents"][0] if personal_results["documents"] else []
    all_chunks = company_chunks + personal_chunks

    if not all_chunks:
        return (
            "Desculpe, não encontrei nenhum documento na base de conhecimento que responda "
            "à sua pergunta. Se você tem um documento relevante, pode anexá-lo na conversa."
        )

    context = "\n\n---\n\n".join(all_chunks)

    prompt = f"""
Você é um assistente corporativo especializado e prestativo.

Sua missão é responder à pergunta do usuário utilizando APENAS as informações contidas
nos fragmentos de contexto abaixo. Esses fragmentos vêm de documentos da empresa e/ou
documentos pessoais do próprio usuário.

REGRAS IMPORTANTES:
1. Use SOMENTE o contexto fornecido. Nunca invente ou suponha informações.
2. Se a informação não estiver no contexto, responda exatamente:
   "Não encontrei essa informação nos documentos disponíveis. Por favor, verifique com o responsável ou envie um documento mais específico."
3. Seja claro, objetivo e profissional.
4. Se relevante, indique de qual trecho tirou a informação.

Contexto dos documentos:
{context}

Pergunta do usuário:
{user_query}

Resposta:
"""

    response = llm.invoke(prompt)
    return response.content