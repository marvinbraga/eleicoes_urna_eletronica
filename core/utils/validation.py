"""
Módulo de validação robusta de entrada.
Implementa validações de segurança para IDs, strings, arquivos e outros dados.
"""
import os
import re
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile, status


# Tipos de arquivo permitidos
ALLOWED_FILE_EXTENSIONS = {
    'pem': ['.pem'],
    'json': ['.json'],
    'image': ['.jpg', '.jpeg', '.png']
}

# Tamanhos máximos de arquivo (em bytes)
MAX_FILE_SIZES = {
    'pem': 10 * 1024,  # 10 KB
    'json': 1 * 1024 * 1024,  # 1 MB
    'image': 5 * 1024 * 1024  # 5 MB
}


def validate_positive_id(value: int, field_name: str = "id") -> int:
    """
    Valida que um ID é positivo e maior que zero.

    Args:
        value: Valor do ID a ser validado
        field_name: Nome do campo para mensagem de erro

    Returns:
        O valor validado

    Raises:
        HTTPException: Se o ID for inválido
    """
    if not isinstance(value, int):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} deve ser um número inteiro"
        )

    if value <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} deve ser maior que zero"
        )

    return value


def validate_string_length(value: str, min_length: int = 1, max_length: int = 255,
                          field_name: str = "campo") -> str:
    """
    Valida o tamanho de uma string.

    Args:
        value: String a ser validada
        min_length: Tamanho mínimo permitido
        max_length: Tamanho máximo permitido
        field_name: Nome do campo para mensagem de erro

    Returns:
        A string validada

    Raises:
        HTTPException: Se a string não atender aos requisitos
    """
    if not isinstance(value, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} deve ser uma string"
        )

    if len(value) < min_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} deve ter no mínimo {min_length} caracteres"
        )

    if len(value) > max_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} deve ter no máximo {max_length} caracteres"
        )

    return value


def sanitize_filename(filename: str) -> str:
    """
    Sanitiza um nome de arquivo removendo caracteres perigosos.

    Args:
        filename: Nome do arquivo a ser sanitizado

    Returns:
        Nome do arquivo sanitizado
    """
    # Remove path traversal attempts
    filename = os.path.basename(filename)

    # Remove caracteres especiais, mantendo apenas alfanuméricos, pontos, hífens e underscores
    filename = re.sub(r'[^\w\s\.-]', '', filename)

    # Remove espaços múltiplos
    filename = re.sub(r'\s+', '_', filename)

    # Limita o tamanho do nome do arquivo
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext

    return filename


def validate_file_upload(file: UploadFile, file_type: str) -> None:
    """
    Valida um arquivo de upload verificando tipo, extensão e tamanho.

    Args:
        file: Arquivo de upload do FastAPI
        file_type: Tipo esperado do arquivo ('pem', 'json', 'image')

    Raises:
        HTTPException: Se o arquivo não for válido
    """
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum arquivo foi enviado"
        )

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nome do arquivo inválido"
        )

    # Validar extensão
    file_ext = Path(file.filename).suffix.lower()
    if file_type not in ALLOWED_FILE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de arquivo '{file_type}' não suportado"
        )

    allowed_extensions = ALLOWED_FILE_EXTENSIONS[file_type]
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extensão de arquivo inválida. Esperado: {', '.join(allowed_extensions)}"
        )

    # Validar tamanho (se disponível)
    if hasattr(file, 'size') and file.size is not None:
        max_size = MAX_FILE_SIZES.get(file_type, 1 * 1024 * 1024)  # Default 1MB
        if file.size > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Arquivo muito grande. Tamanho máximo: {max_size / 1024 / 1024:.2f} MB"
            )


def validate_codigo_candidato(codigo: str) -> str:
    """
    Valida o formato do código de candidato.

    Args:
        codigo: Código do candidato a ser validado

    Returns:
        Código validado

    Raises:
        HTTPException: Se o código for inválido
    """
    # Código de candidato deve ter 2-5 dígitos numéricos
    if not codigo.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código do candidato deve conter apenas números"
        )

    if len(codigo) < 2 or len(codigo) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código do candidato deve ter entre 2 e 5 dígitos"
        )

    return codigo


def validate_json_keys(data: dict, required_keys: list[str], optional_keys: Optional[list[str]] = None) -> None:
    """
    Valida que um dicionário JSON contém as chaves necessárias.

    Args:
        data: Dicionário a ser validado
        required_keys: Lista de chaves obrigatórias
        optional_keys: Lista de chaves opcionais permitidas

    Raises:
        HTTPException: Se faltar alguma chave obrigatória ou houver chaves não permitidas
    """
    if not isinstance(data, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dados inválidos: esperado objeto JSON"
        )

    # Verificar chaves obrigatórias
    missing_keys = set(required_keys) - set(data.keys())
    if missing_keys:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Chaves obrigatórias faltando: {', '.join(missing_keys)}"
        )

    # Verificar chaves extras (se lista de opcionais foi fornecida)
    if optional_keys is not None:
        allowed_keys = set(required_keys) | set(optional_keys)
        extra_keys = set(data.keys()) - allowed_keys
        if extra_keys:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Chaves não permitidas: {', '.join(extra_keys)}"
            )
