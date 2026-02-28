from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from backend.vector_store.chroma_client import get_chroma_collection

embedding_model = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)


def generate_answer(
    user_query: str,
    user_id: int,
    conversation_history: list | None = None
) -> str:
    """
    Busca contexto no banco vetorial com filtro MULTI-ESCOPO e gera a resposta.

    Estratégia de busca:
    - Documentos da empresa (scope='company'): acessíveis por todos.
    - Documentos pessoais (scope='personal', user_id=<user_id>): apenas do usuário.

    O usuário não precisa selecionar nenhum documento — a IA busca em tudo
    que é relevante automaticamente.

    conversation_history: lista de dicts {"query": str, "response": str}
    com as mensagens anteriores do usuário (mais antigas primeiro).
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
        context_section = "(Nenhum documento encontrado na base de conhecimento.)"
        has_context = False
    else:
        context_section = "\n\n---\n\n".join(all_chunks)
        has_context = True

    # ── Histórico de conversa ──
    history_section = ""
    if conversation_history:
        turns = []
        for turn in conversation_history:
            turns.append(f"Usuário: {turn['query']}")
            turns.append(f"Assistente: {turn['response']}")
        history_section = (
            "Histórico da conversa (mensagens anteriores, da mais antiga para a mais recente):\n"
            + "\n".join(turns)
            + "\n"
        )

    prompt = f"""
Você é um assistente corporativo especializado, inteligente e prestativo.

Você tem acesso a fragmentos de documentos da empresa e/ou documentos pessoais do usuário.
Sua missão é ajudar o usuário da melhor forma possível, seguindo estas regras:

1. Se a pergunta pode ser respondida pelos documentos fornecidos, priorize SEMPRE o conteúdo dos documentos.
2. Se os documentos são parcialmente relevantes, combine-os com seu conhecimento geral para dar uma resposta completa. Indique claramente o que vem do documento e o que é conhecimento geral.
3. Se a pergunta for completamente independente dos documentos (ex: perguntas gerais, pedidos de criação de conteúdo, dúvidas genéricas), responda normalmente usando seu conhecimento. Não invente informações sobre a empresa sem base nos documentos.
4. Nunca invente dados específicos da empresa (números, nomes, regras) que não estejam nos documentos.
5. Você tem memória do histórico desta conversa. Use-o para entender referências como "meu nome", "aquela história que contei", "o que falei antes", etc.

{history_section}
Fragmentos dos documentos disponíveis:
{context_section}

Pergunta atual do usuário:
{user_query}

Resposta:
"""

    response = llm.invoke(prompt)
    return response.content