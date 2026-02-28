import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.models.models import Document, User
from backend.services.document_processor import process_and_store_pdf
from backend.core.deps import get_current_user, get_admin_user

router = APIRouter(prefix="/documents", tags=["Documentos"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload/company")
def upload_company_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)  # Somente ADMIN
):
    """
    [ADMIN] Faz upload de um documento para a base da empresa.
    Disponível como contexto para TODOS os usuários ao consultarem o assistente.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são permitidos.")

    file_path = os.path.join(UPLOAD_DIR, f"company_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    new_document = Document(
        filename=file.filename,
        file_path=file_path,
        scope="company",
        user_id=current_user.id
    )
    db.add(new_document)
    db.commit()
    db.refresh(new_document)

    try:
        process_and_store_pdf(
            file_path=new_document.file_path,
            document_id=new_document.id,
            scope="company",
            owner_user_id=current_user.id
        )
    except Exception as e:
        db.delete(new_document)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Erro ao processar o PDF: {str(e)}")

    return {
        "message": "Documento da empresa indexado com sucesso!",
        "document_id": new_document.id,
        "filename": new_document.filename,
        "scope": "company"
    }


@router.post("/upload/personal")
def upload_personal_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Faz upload de um documento pessoal do usuário.
    Visível apenas para o próprio usuário, complementa a base da empresa.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são permitidos.")

    file_path = os.path.join(UPLOAD_DIR, f"user_{current_user.id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    new_document = Document(
        filename=file.filename,
        file_path=file_path,
        scope="personal",
        user_id=current_user.id
    )
    db.add(new_document)
    db.commit()
    db.refresh(new_document)

    try:
        process_and_store_pdf(
            file_path=new_document.file_path,
            document_id=new_document.id,
            scope="personal",
            owner_user_id=current_user.id
        )
    except Exception as e:
        db.delete(new_document)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Erro ao processar o PDF: {str(e)}")

    return {
        "message": "Documento pessoal indexado com sucesso!",
        "document_id": new_document.id,
        "filename": new_document.filename,
        "scope": "personal"
    }


@router.get("/company")
def list_company_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista todos os documentos da base da empresa."""
    docs = db.query(Document).filter(Document.scope == "company").all()
    return [
        {"id": d.id, "filename": d.filename, "uploaded_at": d.uploaded_at}
        for d in docs
    ]


@router.get("/personal")
def list_personal_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista os documentos pessoais do usuário autenticado."""
    docs = (
        db.query(Document)
        .filter(Document.scope == "personal", Document.user_id == current_user.id)
        .all()
    )
    return [
        {"id": d.id, "filename": d.filename, "uploaded_at": d.uploaded_at}
        for d in docs
    ]


@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Remove um documento. Admins removem qualquer documento.
    Usuários só removem seus próprios documentos pessoais.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento não encontrado.")

    if current_user.role != "admin" and doc.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sem permissão para remover este documento.")

    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    db.delete(doc)
    db.commit()
    return {"message": "Documento removido com sucesso."}