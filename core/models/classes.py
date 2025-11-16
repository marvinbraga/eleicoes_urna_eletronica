# models/classes.py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Partido(BaseModel):
    numero: int = Field(..., description="Número do partido")
    sigla: str = Field(..., description="Sigla do partido")
    nome: str = Field(..., description="Nome completo do partido")


class Cargo(BaseModel):
    id: int = Field(..., description="ID único do cargo")
    nome: str = Field(..., description="Nome do cargo")
    eleicao: int = Field(..., description="ID da eleição a qual o cargo pertence")


class Eleicao(BaseModel):
    id: int = Field(..., description="ID único da eleição")
    nome: str = Field(..., description="Nome da eleição")
    data: datetime = Field(..., description="Data da eleição")
    turnos: int = Field(..., description="Número de turnos da eleição (1 ou 2)")


class Candidato(BaseModel):
    id: int = Field(..., description="ID único do candidato")
    nome: str = Field(..., description="Nome completo do candidato")
    partido: Partido = Field(..., description="Partido político do candidato")
    codigo: str = Field(..., description="Código do candidato (prefixo do partido + código específico)")
    foto: str = Field(..., description="URL da foto do candidato")
    cargo: Cargo = Field(..., description="Cargo ao qual o candidato está concorrendo")
    eleicao: Eleicao = Field(..., description="Eleição da qual o candidato está participando")


class Voto(BaseModel):
    id: str = Field(..., description="ID único do voto (UUID)")
    candidato: Candidato = Field(..., description="Candidato votado")
    hash_localizacao: str = Field(..., description="Hash de localização do voto na listagem de votos da urna")
    hash_blockchain: str = Field(..., description="Hash do registro do voto no Blockchain")
    qr_code: str = Field(..., description="QR Code contendo todas as informações do voto")
    data_hora: datetime = Field(default_factory=datetime.now, description="Data e hora do voto")
    nonce: str = Field(None, description="Nonce único para prevenir duplicação de votos")


class RegistroImpresso(BaseModel):
    voto: Voto = Field(..., description="Voto registrado")
    data_hora: datetime = Field(..., description="Data e hora da impressão do registro")


class BoletimUrna(BaseModel):
    id: int = Field(..., description="ID único do Boletim de Urna")
    secao: str = Field(..., description="Seção eleitoral")
    zona: str = Field(..., description="Zona eleitoral")
    municipio: str = Field(..., description="Município da urna")
    estado: str = Field(..., description="Estado da urna")
    data_hora: datetime = Field(..., description="Data e hora da geração do Boletim de Urna")
    hash_final_blockchain: str = Field(..., description="Hash final do Blockchain dos votos da urna")
    hash_bu: str = Field(..., description="Hash das informações do Boletim de Urna")
    qr_code: str = Field(..., description="QR Code contendo os hashes e informações do Boletim de Urna")
    votos: list[Voto] = Field(..., description="Lista de votos registrados na urna")
    assinatura: str = Field(None, description="Assinatura digital do Boletim de Urna")

    @field_validator('secao')
    @classmethod
    def validate_secao(cls, v: str) -> str:
        """
        Valida o formato da seção eleitoral.
        Formato esperado: "Seção" seguido de número ou nome.
        """
        if not v or len(v.strip()) < 3:
            raise ValueError('Seção deve ter no mínimo 3 caracteres')
        return v.strip()

    @field_validator('zona')
    @classmethod
    def validate_zona(cls, v: str) -> str:
        """
        Valida o formato da zona eleitoral.
        Formato esperado: "Zona" seguido de número.
        """
        if not v or len(v.strip()) < 3:
            raise ValueError('Zona deve ter no mínimo 3 caracteres')
        return v.strip()

    @field_validator('municipio')
    @classmethod
    def validate_municipio(cls, v: str) -> str:
        """
        Valida o nome do município.
        """
        if not v or len(v.strip()) < 3:
            raise ValueError('Município deve ter no mínimo 3 caracteres')
        if not all(c.isalpha() or c.isspace() for c in v):
            raise ValueError('Município deve conter apenas letras e espaços')
        return v.strip()

    @field_validator('estado')
    @classmethod
    def validate_estado(cls, v: str) -> str:
        """
        Valida o nome ou sigla do estado.
        """
        if not v or len(v.strip()) < 2:
            raise ValueError('Estado deve ter no mínimo 2 caracteres')

        # Lista de siglas válidas dos estados brasileiros
        siglas_validas = [
            'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
            'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
            'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
        ]

        v_upper = v.strip().upper()

        # Aceita siglas válidas ou nomes de estados
        if len(v_upper) == 2 and v_upper not in siglas_validas:
            raise ValueError(f'Sigla de estado inválida: {v}. Use uma sigla válida: {", ".join(siglas_validas)}')

        return v.strip()


class RegistroUrna(BaseModel):
    id: int = Field(..., description="ID único do Registro de Urna")
    data_hora: datetime = Field(..., description="Data e hora da geração do Registro de Urna")
    boletim_urna_escaneado: bytes = Field(..., description="Boletim de Urna escaneado e assinado pelas autoridades")
    boletim_urna_eletronico: BoletimUrna = Field(..., description="Boletim de Urna eletrônico validado")


class TotalizacaoVotos(BaseModel):
    id: int = Field(..., description="ID único da Totalização de Votos")
    data_hora: datetime = Field(..., description="Data e hora da totalização dos votos")
    votos_totalizados: list[Voto] = Field(..., description="Lista de votos totalizados")
    hash_blockchain: str = Field(..., description="Hash do Blockchain da totalização dos votos")
    assinatura: str = Field(None, description="Assinatura digital da Totalização de Votos")


class User(BaseModel):
    """Modelo de usuário para autenticação"""
    username: str = Field(..., min_length=3, max_length=50, description="Nome de usuário único")
    email: str = Field(..., description="Email do usuário")
    full_name: Optional[str] = Field(None, max_length=100, description="Nome completo do usuário")
    disabled: bool = Field(default=False, description="Indica se o usuário está desabilitado")
    scopes: list[str] = Field(default_factory=list, description="Permissões do usuário")

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        """Valida que o username contém apenas caracteres alfanuméricos e underscore"""
        if not v.replace('_', '').isalnum():
            raise ValueError('Username deve conter apenas letras, números e underscore')
        return v


class UserInDB(User):
    """Modelo de usuário armazenado no banco de dados (inclui hash da senha)"""
    hashed_password: str = Field(..., description="Hash bcrypt da senha do usuário")


class UserCreate(BaseModel):
    """Modelo para criação de usuário"""
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=8, max_length=100)
    full_name: Optional[str] = Field(None, max_length=100)
    scopes: list[str] = Field(default_factory=list)

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Valida força da senha"""
        if len(v) < 8:
            raise ValueError('Senha deve ter no mínimo 8 caracteres')
        if not any(char.isdigit() for char in v):
            raise ValueError('Senha deve conter pelo menos um número')
        if not any(char.isupper() for char in v):
            raise ValueError('Senha deve conter pelo menos uma letra maiúscula')
        return v


class LoginRequest(BaseModel):
    """Modelo para requisição de login"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=1, max_length=100)
