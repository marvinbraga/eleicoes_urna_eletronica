"""
Configurações do sistema de votação eletrônica.
"""
import os
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class VotingSystemSettings:
    """
    Configurações do sistema de votação.
    Valores podem ser sobrescritos por variáveis de ambiente.
    """

    # Informações da urna
    secao: str = field(default_factory=lambda: os.getenv("SECAO", "Seção XYZ"))
    zona: str = field(default_factory=lambda: os.getenv("ZONA", "Zona 123"))
    municipio: str = field(default_factory=lambda: os.getenv("MUNICIPIO", "Município ABC"))
    estado: str = field(default_factory=lambda: os.getenv("ESTADO", "Estado MN"))

    # Configurações de criptografia
    chave_privada_path: str = field(default_factory=lambda: os.getenv("CHAVE_PRIVADA_PATH", "resources/chave_privada.pem"))
    chave_criptografia_path: str = field(default_factory=lambda: os.getenv("CHAVE_CRIPTOGRAFIA_PATH", "resources/chave_criptografia.key"))

    # Configurações de auditoria
    audit_log_dir: str = field(default_factory=lambda: os.getenv("AUDIT_LOG_DIR", "security"))

    # Configurações de banco de dados (se houver)
    database_url: Optional[str] = field(default_factory=lambda: os.getenv("DATABASE_URL"))

    # Configurações de API
    api_host: str = field(default_factory=lambda: os.getenv("API_HOST", "0.0.0.0"))
    api_port: int = field(default_factory=lambda: int(os.getenv("API_PORT", "8000")))
    api_reload: bool = field(default_factory=lambda: os.getenv("API_RELOAD", "false").lower() == "true")


# Instância global de configurações
settings = VotingSystemSettings()
