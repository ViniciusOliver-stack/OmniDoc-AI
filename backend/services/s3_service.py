"""
Serviço centralizado para operações no AWS S3.

Todas as interações com o bucket (upload, download, delete, geração de URL)
estão aqui para facilitar manutenção e testes.
"""
import io
import boto3
from botocore.exceptions import ClientError

from backend.core.config import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_REGION,
    S3_BUCKET_NAME,
)


def _get_client():
    """Retorna um cliente S3 autenticado."""
    return boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )


def upload_file_to_s3(file_bytes: bytes, s3_key: str, content_type: str = "application/pdf") -> str:
    """
    Faz upload de bytes para o bucket S3.

    Args:
        file_bytes: conteúdo do arquivo em bytes
        s3_key:     caminho dentro do bucket, ex: 'company/relatorio.pdf'
        content_type: MIME type do arquivo

    Returns:
        s3_key (usado como referência para download/delete futuro)
    """
    client = _get_client()
    client.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=s3_key,
        Body=file_bytes,
        ContentType=content_type,
    )
    return s3_key


def download_file_from_s3(s3_key: str) -> bytes:
    """
    Baixa um arquivo do S3 e retorna como bytes.

    Args:
        s3_key: caminho dentro do bucket (mesmo valor salvo no banco)

    Returns:
        conteúdo do arquivo em bytes
    """
    client = _get_client()
    response = client.get_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
    return response["Body"].read()


def delete_file_from_s3(s3_key: str) -> None:
    """
    Remove um arquivo do bucket S3.

    Args:
        s3_key: caminho dentro do bucket (mesmo valor salvo no banco)
    """
    client = _get_client()
    try:
        client.delete_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
    except ClientError as e:
        # Loga mas não levanta exceção — o arquivo pode já ter sido removido manualmente
        print(f"[S3] Aviso ao deletar '{s3_key}': {e}")


def generate_presigned_url(s3_key: str, expiration_seconds: int = 3600) -> str:
    """
    Gera uma URL temporária e assinada para acesso direto ao arquivo
    (útil para download ou preview futuro na interface).

    Args:
        s3_key:             caminho dentro do bucket
        expiration_seconds: tempo de validade em segundos (padrão: 1h)

    Returns:
        URL assinada como string
    """
    client = _get_client()
    url = client.generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET_NAME, "Key": s3_key},
        ExpiresIn=expiration_seconds,
    )
    return url
