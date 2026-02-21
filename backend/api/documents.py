import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

# Importamos a função que abre conexão com o banco de dados
from backend.db.database import get_db
from backend.models.models import Document, User

router = APIRouter()

# Difinir a pasta onde os arquivos serão salvos
UPLOAD_DIR = "uploads"

# cria a pasta automaticamente se não existir
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/documents/upload/")
def upload_document(
    # O id do usuário como um campo de formulário (não parte do arquivo)
    user_id: int = Form(...),
    # Recebemos o arquivo próprio dito
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    #1. Verificar se o arquivo é realmente um PDF
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são permitidos.")
    
    #2. Verificar se o usuário existe no Banco de dados
    user = db.query(User).filter(User.id == user_id).first()
    if not user: 
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    
    #3. Salvar o arquivo fisicamente na pasta "uploads"
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    # Abrimos um arquivo vazio no nosso computador e copiamos o conteúdo do PDF para ele
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    #4. Salvar os metadados (Informações) no PostgreSQL
    new_document = Document(
        filename=file.filename,
        file_path=file_path,
        user_id=user_id
    )
    
    db.add(new_document)  # "Anota" a intenção de inserir o documento
    db.commit()           # Executa a inserção no banco de dados
    db.refresh(new_document)  # Atualiza o objeto com os dados do banco (ex: id gerado)
    
    # Retornamos uma mensagem de sucesso com os dados do documento
    return {
        "message": "Upload Realizado com sucesso!",
        "document_id": new_document.id,
        "filename": new_document.filename,
    }