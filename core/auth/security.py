"""
Módulo de segurança para autenticação e autorização JWT.
Implementa funções para geração, validação de tokens e hash de senhas.
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# Configurações JWT
SECRET_KEY = "your-secret-key-here-change-in-production"  # DEVE ser movido para variável de ambiente
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Contexto para hash de senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class Token(BaseModel):
    """Modelo de resposta de token JWT"""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Modelo de dados extraídos do token JWT"""
    username: Optional[str] = None
    scopes: list[str] = []


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se a senha em texto plano corresponde ao hash armazenado.

    Args:
        plain_password: Senha em texto plano
        hashed_password: Hash da senha armazenado no banco

    Returns:
        True se a senha corresponder, False caso contrário
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Gera um hash bcrypt seguro para a senha.

    Args:
        password: Senha em texto plano

    Returns:
        Hash bcrypt da senha
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Cria um token JWT com os dados fornecidos.

    Args:
        data: Dados a serem codificados no token
        expires_delta: Tempo de expiração customizado (opcional)

    Returns:
        Token JWT codificado
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> TokenData:
    """
    Decodifica e valida um token JWT.

    Args:
        token: Token JWT a ser decodificado

    Returns:
        TokenData com os dados extraídos do token

    Raises:
        HTTPException: Se o token for inválido ou expirado
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        scopes = payload.get("scopes", [])
        token_data = TokenData(username=username, scopes=scopes)
        return token_data
    except JWTError:
        raise credentials_exception


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Dependency para obter o usuário atual a partir do token JWT.

    Args:
        token: Token JWT extraído do header Authorization

    Returns:
        TokenData com informações do usuário autenticado

    Raises:
        HTTPException: Se o token for inválido
    """
    return decode_access_token(token)


def require_scope(required_scope: str):
    """
    Factory para criar dependency que verifica se o usuário tem o escopo necessário.

    Args:
        required_scope: Escopo necessário para acessar o recurso

    Returns:
        Dependency function que valida o escopo
    """
    async def scope_checker(token_data: TokenData = Depends(get_current_user)):
        if required_scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permissão insuficiente. Escopo '{required_scope}' necessário."
            )
        return token_data
    return scope_checker
