"""
Módulo de logging seguro.
Implementa funções para sanitizar logs e prevenir vazamento de informações sensíveis.
"""
import re
from typing import Any, Dict


# Padrões de dados sensíveis a serem mascarados
SENSITIVE_PATTERNS = {
    'hash': r'([a-f0-9]{64})',  # SHA-256 hash
    'nonce': r'(nonce["\']?\s*:\s*["\']?[a-f0-9]+)',
    'password': r'(password["\']?\s*:\s*["\'][^"\']+["\'])',
    'token': r'(token["\']?\s*:\s*["\'][^"\']+["\'])',
    'authorization': r'(Authorization["\']?\s*:\s*["\']?Bearer\s+[^"\']+)',
}


def mask_sensitive_data(text: str, mask_char: str = "*", visible_chars: int = 4) -> str:
    """
    Mascara dados sensíveis em uma string de log.

    Args:
        text: Texto a ser sanitizado
        mask_char: Caractere usado para mascarar dados sensíveis
        visible_chars: Número de caracteres visíveis no início e fim

    Returns:
        Texto com dados sensíveis mascarados
    """
    if not text:
        return text

    sanitized_text = text

    # Mascarar hashes completos (mostrar apenas início e fim)
    def mask_hash(match):
        hash_value = match.group(1)
        if len(hash_value) > visible_chars * 2:
            return f"{hash_value[:visible_chars]}...{hash_value[-visible_chars:]}"
        return mask_char * len(hash_value)

    sanitized_text = re.sub(SENSITIVE_PATTERNS['hash'], mask_hash, sanitized_text)

    # Mascarar completamente nonce, passwords, tokens
    for key in ['nonce', 'password', 'token', 'authorization']:
        if key in SENSITIVE_PATTERNS:
            sanitized_text = re.sub(
                SENSITIVE_PATTERNS[key],
                lambda m: f"{key}: {mask_char * 8}",
                sanitized_text,
                flags=re.IGNORECASE
            )

    return sanitized_text


def sanitize_log_dict(data: Dict[str, Any], sensitive_keys: list[str] = None) -> Dict[str, Any]:
    """
    Sanitiza um dicionário removendo ou mascarando chaves sensíveis.

    Args:
        data: Dicionário a ser sanitizado
        sensitive_keys: Lista de chaves adicionais a serem consideradas sensíveis

    Returns:
        Dicionário sanitizado
    """
    if not isinstance(data, dict):
        return data

    # Chaves sensíveis padrão
    default_sensitive_keys = [
        'password', 'senha', 'token', 'secret', 'api_key',
        'private_key', 'hashed_password', 'nonce'
    ]

    if sensitive_keys:
        default_sensitive_keys.extend(sensitive_keys)

    sanitized = {}
    for key, value in data.items():
        # Se a chave é sensível, mascarar o valor
        if any(sensitive in key.lower() for sensitive in default_sensitive_keys):
            sanitized[key] = "***REDACTED***"
        # Se o valor é um hash (64 caracteres hexadecimais), mascarar
        elif isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value.lower()):
            sanitized[key] = f"{value[:4]}...{value[-4:]}"
        # Se o valor é um dicionário, sanitizar recursivamente
        elif isinstance(value, dict):
            sanitized[key] = sanitize_log_dict(value, sensitive_keys)
        # Se o valor é uma lista, sanitizar cada elemento
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_log_dict(item, sensitive_keys) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            sanitized[key] = value

    return sanitized


def get_safe_error_message(error: Exception, debug_mode: bool = False) -> str:
    """
    Retorna uma mensagem de erro segura para enviar ao cliente.

    Args:
        error: Exceção original
        debug_mode: Se True, inclui detalhes do erro (apenas para desenvolvimento)

    Returns:
        Mensagem de erro segura
    """
    if debug_mode:
        return str(error)

    # Em produção, retornar mensagens genéricas
    error_type = type(error).__name__

    generic_messages = {
        'ValidationError': 'Dados de entrada inválidos',
        'FileNotFoundError': 'Recurso não encontrado',
        'PermissionError': 'Permissão negada',
        'ValueError': 'Valor inválido fornecido',
        'KeyError': 'Campo obrigatório ausente',
        'TypeError': 'Tipo de dado incorreto',
        'ConnectionError': 'Erro de conexão com serviço externo',
        'TimeoutError': 'Operação excedeu o tempo limite',
    }

    return generic_messages.get(error_type, 'Erro interno do servidor')


def log_request_safely(method: str, path: str, params: dict = None, body: dict = None) -> dict:
    """
    Prepara dados de requisição para log de forma segura.

    Args:
        method: Método HTTP
        path: Caminho da requisição
        params: Parâmetros da query string
        body: Corpo da requisição

    Returns:
        Dicionário com dados sanitizados para log
    """
    log_data = {
        'method': method,
        'path': path,
    }

    if params:
        log_data['params'] = sanitize_log_dict(params)

    if body:
        log_data['body'] = sanitize_log_dict(body)

    return log_data
