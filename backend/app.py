import json
import os
import stat
from datetime import datetime, timedelta
from typing import Optional

import redis
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, Request, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from core.auth.security import (
    create_access_token, verify_password, get_password_hash,
    get_current_user, Token, require_scope
)
from core.models.classes import (
    Eleicao, Partido, Cargo, Candidato, Voto, TotalizacaoVotos,
    User, UserInDB, UserCreate, LoginRequest
)
from core.processors.classes import SistemaVotacao
from core.utils.qr_code_gen import QRCodeService
from core.utils.validation import (
    validate_positive_id, validate_file_upload, sanitize_filename,
    validate_codigo_candidato
)
from core.utils.secure_logging import (
    mask_sensitive_data, sanitize_log_dict, get_safe_error_message
)


# Modelo para receber dados de voto do frontend
class VotoRequest(BaseModel):
    candidato: Candidato


# Carregar variáveis de ambiente
load_dotenv()

# Configurações de ambiente
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:7000")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_SOCKET_TIMEOUT = int(os.getenv("REDIS_SOCKET_TIMEOUT", "5"))
REDIS_SOCKET_CONNECT_TIMEOUT = int(os.getenv("REDIS_SOCKET_CONNECT_TIMEOUT", "5"))

# Configurações CORS
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost,http://localhost:7000").split(",")
CORS_ALLOW_CREDENTIALS = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
CORS_ALLOW_METHODS = os.getenv("CORS_ALLOW_METHODS", "GET,POST,PUT,DELETE").split(",")
CORS_ALLOW_HEADERS = os.getenv("CORS_ALLOW_HEADERS", "Content-Type,Authorization").split(",")

# Modo debug
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

# Configuração de logging seguro
logger.info(f"BACKEND_URL: {BACKEND_URL}")
logger.info(f"REDIS_HOST: {REDIS_HOST}")
logger.info(f"REDIS_PORT: {REDIS_PORT}")
logger.info(f"DEBUG_MODE: {DEBUG_MODE}")

# Configurar Redis com timeouts
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True,
    socket_timeout=REDIS_SOCKET_TIMEOUT,
    socket_connect_timeout=REDIS_SOCKET_CONNECT_TIMEOUT,
    socket_keepalive=True,
    health_check_interval=30
)

# Configurar rate limiting
limiter = Limiter(key_func=get_remote_address)

# Configurar Jinja2 templates
templates = Jinja2Templates(directory="backend/templates")
app = FastAPI(templates=templates)

# Adicionar rate limiting ao app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configurar CORS com validação de origem
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    allow_methods=CORS_ALLOW_METHODS,
    allow_headers=CORS_ALLOW_HEADERS,
)

# Montar o diretório de arquivos estáticos
app.mount("/static", StaticFiles(directory="backend/static"), name="static")

# Diretório para salvar os arquivos de chave com permissões seguras
UPLOAD_DIRECTORY = "uploaded_keys"


def setup_secure_directory():
    """Cria o diretório de upload com permissões seguras (0o700)"""
    if not os.path.exists(UPLOAD_DIRECTORY):
        os.makedirs(UPLOAD_DIRECTORY)
        # Define permissões apenas para o proprietário (rwx------)
        os.chmod(UPLOAD_DIRECTORY, stat.S_IRWXU)
        logger.info(f"Diretório {UPLOAD_DIRECTORY} criado com permissões 0o700")
    else:
        # Verificar e corrigir permissões se necessário
        current_permissions = stat.S_IMODE(os.stat(UPLOAD_DIRECTORY).st_mode)
        if current_permissions != stat.S_IRWXU:
            os.chmod(UPLOAD_DIRECTORY, stat.S_IRWXU)
            logger.warning(f"Permissões do diretório {UPLOAD_DIRECTORY} corrigidas para 0o700")


# Instância do serviço de QR Code
qr_code_service = QRCodeService()


# Dependency injection para sistema de votação
def get_sistema_votacao() -> SistemaVotacao:
    """
    Dependency para obter a instância do sistema de votação.

    Returns:
        Instância do SistemaVotacao

    Raises:
        HTTPException: Se o sistema não foi inicializado
    """
    if not hasattr(app.state, 'sistema_votacao') or app.state.sistema_votacao is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sistema de votação não inicializado. Faça o upload das chaves primeiro."
        )
    return app.state.sistema_votacao


# Handler global de exceções
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Handler global para capturar exceções não tratadas.
    Em produção, não expõe stacktraces aos clientes.
    """
    # Logar o erro completo no servidor
    logger.error(f"Erro não tratado: {type(exc).__name__}: {str(exc)}", exc_info=True)

    # Retornar mensagem segura ao cliente
    error_message = get_safe_error_message(exc, debug_mode=DEBUG_MODE)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": error_message}
    )


# Evento de startup
@app.on_event("startup")
async def startup_event():
    """Configurações executadas ao iniciar a aplicação"""
    setup_secure_directory()
    app.state.sistema_votacao = None
    logger.info("Aplicação iniciada com sucesso")


# ==================== ENDPOINTS DE AUTENTICAÇÃO ====================

@app.post("/api/auth/login", response_model=Token)
@limiter.limit("5/minute")
async def login(request: Request, login_data: LoginRequest):
    """
    Endpoint de login que retorna um token JWT.

    Rate limit: 5 requisições por minuto
    """
    # TODO: Implementar busca real de usuário no banco de dados
    # Por enquanto, usuário de exemplo para demonstração
    fake_user = UserInDB(
        username="admin",
        email="admin@urna.gov.br",
        full_name="Administrador do Sistema",
        hashed_password=get_password_hash("Admin123"),  # Senha: Admin123
        scopes=["admin", "votacao", "totalizacao"]
    )

    # Verificar se usuário existe e senha está correta
    if login_data.username != fake_user.username:
        logger.warning(f"Tentativa de login com usuário inexistente: {login_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(login_data.password, fake_user.hashed_password):
        logger.warning(f"Tentativa de login com senha incorreta para usuário: {login_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Criar token JWT
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": fake_user.username, "scopes": fake_user.scopes},
        expires_delta=access_token_expires
    )

    logger.info(f"Login bem-sucedido para usuário: {login_data.username}")

    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/auth/me")
async def read_users_me(current_user = Depends(get_current_user)):
    """Retorna informações do usuário autenticado"""
    return current_user


# ==================== ENDPOINTS PÚBLICOS ====================

@app.get("/")
async def get_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "BACKEND_URL": BACKEND_URL})


@app.get("/urna.html")
async def get_urna(request: Request):
    return templates.TemplateResponse("urna.html", {"request": request, "BACKEND_URL": BACKEND_URL})


@app.get("/escrutinio.html")
async def get_escrutinio(request: Request):
    return templates.TemplateResponse("escrutinio.html", {"request": request, "BACKEND_URL": BACKEND_URL})


# ==================== ENDPOINTS DE CONFIGURAÇÃO ====================

@app.post("/upload-keys")
@limiter.limit("3/minute")
async def upload_keys(
    request: Request,
    cryptography_key: UploadFile = File(...),
    private_key: UploadFile = File(...),
    election_data: UploadFile = File(...)
):
    """
    Endpoint para upload de chaves criptográficas e dados da eleição.

    Rate limit: 3 requisições por minuto
    Validações:
    - Tipo de arquivo (PEM, JSON)
    - Tamanho máximo de arquivo
    - Sanitização de nome de arquivo
    """
    try:
        # Validar arquivos de upload
        validate_file_upload(cryptography_key, 'pem')
        validate_file_upload(private_key, 'pem')
        validate_file_upload(election_data, 'json')

        # Sanitizar nomes de arquivo
        cryptography_key_filename = sanitize_filename("cryptography_key.pem")
        private_key_filename = sanitize_filename("private_key.pem")

        # Salvar as chaves de segurança
        cryptography_key_path = os.path.join(UPLOAD_DIRECTORY, cryptography_key_filename)
        private_key_path = os.path.join(UPLOAD_DIRECTORY, private_key_filename)

        # Ler e validar tamanho dos arquivos
        crypto_content = await cryptography_key.read()
        private_content = await private_key.read()
        election_content = await election_data.read()

        # Validar tamanhos
        if len(crypto_content) > 10 * 1024:  # 10KB
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Arquivo de chave criptográfica muito grande"
            )

        if len(private_content) > 10 * 1024:  # 10KB
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Arquivo de chave privada muito grande"
            )

        if len(election_content) > 1 * 1024 * 1024:  # 1MB
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Arquivo de dados da eleição muito grande"
            )

        # Salvar arquivos
        with open(cryptography_key_path, "wb") as f:
            f.write(crypto_content)
        # Definir permissões restritas para o arquivo de chave
        os.chmod(cryptography_key_path, stat.S_IRUSR | stat.S_IWUSR)

        with open(private_key_path, "wb") as f:
            f.write(private_content)
        # Definir permissões restritas para o arquivo de chave
        os.chmod(private_key_path, stat.S_IRUSR | stat.S_IWUSR)

        # Processar o arquivo JSON da eleição
        data = json.loads(election_content)

        # Inicializar os dados da eleição
        eleicao = Eleicao(**data['eleicao'])
        partidos = [Partido(**partido) for partido in data['partidos']]
        cargos = [Cargo(**cargo) for cargo in data['cargos']]
        candidatos = [Candidato(**candidato) for candidato in data['candidatos']]

        # Salvar os dados no Redis
        redis_client.set(f"eleicao:{eleicao.id}", eleicao.json())
        for partido in partidos:
            redis_client.set(f"partido:{partido.numero}", partido.json())
        for cargo in cargos:
            redis_client.set(f"cargo:{cargo.id}", cargo.json())
        for candidato in candidatos:
            redis_client.set(f"candidato:{candidato.id}", candidato.json())

        # Inicializar o sistema de votação com as chaves carregadas
        app.state.sistema_votacao = SistemaVotacao(private_key_path, cryptography_key_path)
        logger.info("Sistema de votação inicializado com sucesso!")

        return JSONResponse(content={"message": "Chaves e dados da eleição enviados com sucesso!"}, status_code=200)
    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao decodificar JSON: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arquivo JSON inválido"
        )
    except Exception as e:
        logger.error(f"Erro ao fazer upload das chaves: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_safe_error_message(e, debug_mode=DEBUG_MODE)
        )


@app.get("/keys-status")
async def keys_status():
    """Verifica se as chaves de criptografia foram carregadas"""
    cryptography_key_path = os.path.join(UPLOAD_DIRECTORY, "cryptography_key.pem")
    private_key_path = os.path.join(UPLOAD_DIRECTORY, "private_key.pem")

    keys_exist = os.path.exists(cryptography_key_path) and os.path.exists(private_key_path)
    return JSONResponse(content={"keys_exist": keys_exist}, status_code=200)


# ==================== ENDPOINTS DE CONSULTA ====================

@app.get("/cargos/{eleicao_id}")
async def listar_cargos(eleicao_id: int):
    """Lista todos os cargos de uma eleição"""
    try:
        # Validar eleicao_id
        eleicao_id = validate_positive_id(eleicao_id, "eleicao_id")

        cargos = []
        for key in redis_client.scan_iter(f"cargo:*"):
            cargo = json.loads(redis_client.get(key))
            if cargo['eleicao'] == eleicao_id:
                cargos.append(cargo)

        logger.info(f"Listados {len(cargos)} cargos para eleição {eleicao_id}")
        return JSONResponse(content=cargos, status_code=200)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao listar cargos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_safe_error_message(e, debug_mode=DEBUG_MODE)
        )


@app.get("/candidatos/{cargo_id}")
async def listar_candidatos_por_cargo(cargo_id: int):
    """Lista todos os candidatos de um cargo"""
    try:
        # Validar cargo_id
        cargo_id = validate_positive_id(cargo_id, "cargo_id")

        candidatos = []
        for key in redis_client.scan_iter(f"candidato:*"):
            candidato = json.loads(redis_client.get(key))
            if candidato['cargo']['id'] == cargo_id:
                candidatos.append(candidato)

        logger.info(f"Listados {len(candidatos)} candidatos para cargo {cargo_id}")
        return JSONResponse(content=candidatos, status_code=200)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao listar candidatos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_safe_error_message(e, debug_mode=DEBUG_MODE)
        )


@app.get("/buscar-candidatos/{cargo_id}/{codigo}")
async def buscar_candidatos_por_codigo(cargo_id: int, codigo: str):
    """Busca candidatos por código parcial"""
    try:
        # Validar cargo_id e código
        cargo_id = validate_positive_id(cargo_id, "cargo_id")
        codigo = validate_codigo_candidato(codigo)

        candidatos = []
        for key in redis_client.scan_iter(f"candidato:*"):
            candidato = json.loads(redis_client.get(key))
            if candidato['cargo']['id'] == cargo_id and candidato['codigo'].startswith(codigo):
                candidatos.append(candidato)

        logger.info(f"Encontrados {len(candidatos)} candidatos com código {codigo}")
        return JSONResponse(content=candidatos, status_code=200)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar candidatos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_safe_error_message(e, debug_mode=DEBUG_MODE)
        )


# ==================== ENDPOINTS DE VOTAÇÃO ====================

@app.post("/votar")
@limiter.limit("10/minute")
async def votar(
    request: Request,
    voto_request: VotoRequest,
    sistema_votacao: SistemaVotacao = Depends(get_sistema_votacao)
):
    """
    Registra um voto no sistema.

    Rate limit: 10 requisições por minuto
    Requer: Sistema de votação inicializado
    """
    try:
        # Validar ID do candidato
        validate_positive_id(voto_request.candidato.id, "candidato_id")

        # Verificar se o candidato existe no Redis
        candidato_key = f"candidato:{voto_request.candidato.id}"
        if not redis_client.exists(candidato_key):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidato não encontrado")

        # Registrar o voto usando o sistema de votação
        voto = sistema_votacao.votar(voto_request.candidato)

        # Gerar QR code do voto (sem dados sensíveis completos)
        voto_data = {
            "id": voto.id,
            "candidato_id": voto.candidato.id,
            "candidato_nome": voto.candidato.nome,
            "hash_blockchain": f"{voto.hash_blockchain[:8]}...{voto.hash_blockchain[-8:]}",  # Hash parcial
            "data_hora": voto.data_hora.isoformat() if hasattr(voto.data_hora, 'isoformat') else str(voto.data_hora)
        }
        qr_code_base64 = qr_code_service.gerar_qr_code(json.dumps(voto_data))

        # Atualizar o voto com o QR code em base64
        voto.qr_code = f"data:image/png;base64,{qr_code_base64}"

        # Salvar o voto no Redis
        redis_client.rpush(f"votos:{voto_request.candidato.eleicao.id}", voto.json())

        # Log seguro (sem hash completo ou nonce)
        logger.info(f"Voto registrado: ID={voto.id}, Candidato={voto.candidato.nome}")

        # Retornar o voto completo com QR code
        return JSONResponse(
            content={
                "message": "Voto registrado com sucesso!",
                "voto": json.loads(voto.json())
            },
            status_code=200
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao registrar voto: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_safe_error_message(e, debug_mode=DEBUG_MODE)
        )


@app.post("/verificar-voto")
async def verificar_voto(
    qr_code_data: dict,
    sistema_votacao: SistemaVotacao = Depends(get_sistema_votacao)
):
    """Verifica um voto através dos dados do QR code"""
    try:
        # Extrair dados do QR code
        voto_id = qr_code_data.get("id")
        hash_blockchain = qr_code_data.get("hash_blockchain")

        if not voto_id or not hash_blockchain:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dados do QR code inválidos."
            )

        # Verificar se o voto existe na blockchain
        found = False
        for block in sistema_votacao.blockchain.chain:
            # Comparar hash parcial (primeiros e últimos 8 caracteres)
            block_hash_partial = f"{block.hash[:8]}...{block.hash[-8:]}"
            if block_hash_partial == hash_blockchain or block.hash == hash_blockchain:
                found = True
                break

        if found:
            logger.info(f"Voto {voto_id} verificado com sucesso!")
            return JSONResponse(
                content={
                    "valido": True,
                    "message": "Voto verificado com sucesso!",
                    "voto_id": voto_id
                },
                status_code=200
            )
        else:
            logger.warning(f"Voto {voto_id} não encontrado na blockchain!")
            return JSONResponse(
                content={
                    "valido": False,
                    "message": "Voto não encontrado na blockchain.",
                    "voto_id": voto_id
                },
                status_code=200
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao verificar voto: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_safe_error_message(e, debug_mode=DEBUG_MODE)
        )


# ==================== ENDPOINTS DE TOTALIZAÇÃO ====================

@app.get("/totalizar-votos/{eleicao_id}")
@limiter.limit("5/minute")
async def totalizar_votos(
    request: Request,
    eleicao_id: int,
    sistema_votacao: SistemaVotacao = Depends(get_sistema_votacao)
):
    """
    Totaliza os votos de uma eleição.

    Rate limit: 5 requisições por minuto
    Requer: Sistema de votação inicializado
    """
    try:
        # Validar eleicao_id
        eleicao_id = validate_positive_id(eleicao_id, "eleicao_id")

        # Totalizar votos usando o sistema de votação
        totalizacao = sistema_votacao.totalizar_votos()

        logger.info(f"Totalização de votos realizada para eleição {eleicao_id}")

        return JSONResponse(content=json.loads(totalizacao.json()), status_code=200)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao totalizar votos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_safe_error_message(e, debug_mode=DEBUG_MODE)
        )


@app.get("/gerar-boletim-urna")
async def gerar_boletim_urna(sistema_votacao: SistemaVotacao = Depends(get_sistema_votacao)):
    """
    Gera o Boletim de Urna com todos os votos registrados.

    Requer: Sistema de votação inicializado
    """
    try:
        # Gerar boletim de urna
        boletim = sistema_votacao.gerar_boletim_urna()

        logger.info(f"Boletim de Urna gerado: ID={boletim.id}")

        return JSONResponse(content=json.loads(boletim.json()), status_code=200)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao gerar boletim de urna: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_safe_error_message(e, debug_mode=DEBUG_MODE)
        )
