from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.models.models import Document, User
from backend.services.document_processor import process_and_store_pdf
from backend.core.deps import get_current_user, get_admin_user
from backend.vector_store.chroma_client import delete_document_chunks
from backend.services.s3_service import upload_file_to_s3, delete_file_from_s3

router = APIRouter(prefix="/documents", tags=["Documentos"])


@router.post("/upload/company")
async def upload_company_document(
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

    file_bytes = await file.read()
    s3_key = f"company/{file.filename}"
    upload_file_to_s3(file_bytes, s3_key)

    new_document = Document(
        filename=file.filename,
        file_path=s3_key,   # Guardamos a chave S3 no lugar do caminho local
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
async def upload_personal_document(
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

    file_bytes = await file.read()
    s3_key = f"personal/user_{current_user.id}/{file.filename}"
    upload_file_to_s3(file_bytes, s3_key)

    new_document = Document(
        filename=file.filename,
        file_path=s3_key,   # Guardamos a chave S3 no lugar do caminho local
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

    # Remove do S3
    try:
        delete_file_from_s3(doc.file_path)
    except Exception as e:
        print(f"[!] Erro ao remover arquivo do S3: {e}")

    # Remove os chunks do ChromaDB para evitar resultados de documentos deletados
    try:
        delete_document_chunks(doc.id)
    except Exception as e:
        print(f"[!] Erro ao remover chunks do ChromaDB: {e}")

    db.delete(doc)
    db.commit()
    return {"message": "Documento removido com sucesso."}