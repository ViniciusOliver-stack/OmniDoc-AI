from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.db.database import get_db
from backend.models.models import ChatHistory, User
from backend.services.chat_service import generate_answer
from backend.core.deps import get_current_user

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    query: str


@router.post("/")
def ask_question(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Recebe a pergunta do usuário e retorna a resposta da IA baseada em RAG.

    A busca é feita AUTOMATICAMENTE em:
    - Todos os documentos da base da empresa (scope='company')
    - Todos os documentos pessoais do usuário autenticado (scope='personal')

    Não é necessário informar nenhum ID de documento.
    """
    # Carrega os últimos 10 turnos do histórico do usuário para dar memória à IA
    recent_history = (
        db.query(ChatHistory)
        .filter(ChatHistory.user_id == current_user.id)
        .order_by(ChatHistory.created_at.asc())
        .limit(10)
        .all()
    )
    conv_history = [
        {"query": h.user_query, "response": h.ai_response}
        for h in recent_history
    ]

    try:
        ai_response = generate_answer(
            user_query=request.query,
            user_id=current_user.id,
            conversation_history=conv_history
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar resposta: {str(e)}")

    # Salva o histórico sem vincular a um documento específico (multi-escopo)
    new_chat = ChatHistory(
        user_query=request.query,
        ai_response=ai_response,
        user_id=current_user.id,
        document_id=None
    )
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)

    return {
        "chat_id": new_chat.id,
        "query": request.query,
        "response": ai_response
    }


@router.get("/history")
def get_chat_history(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retorna o histórico de conversas do usuário autenticado."""
    history = (
        db.query(ChatHistory)
        .filter(ChatHistory.user_id == current_user.id)
        .order_by(ChatHistory.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": h.id,
            "query": h.user_query,
            "response": h.ai_response,
            "created_at": h.created_at
        }
        for h in reversed(history)
    ]