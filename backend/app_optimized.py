import json
import os
import time
from datetime import datetime
from typing import Optional

import orjson
import redis
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, Request, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger
from pydantic import BaseModel

from core.models.classes import Eleicao, Partido, Cargo, Candidato, Voto
from core.processors.classes import SistemaVotacao
from core.repositories import (
    EleicaoRepository,
    CandidatoRepository,
    CargoRepository,
    VotoRepository
)
from core.utils.cache import cached, get_cache_stats, invalidate_cache
from core.utils.qr_code_gen import QRCodeService


# Modelo para receber dados de voto do frontend
class VotoRequest(BaseModel):
    candidato: Candidato


# Response usando orjson para performance
class ORJSONResponse(Response):
    media_type = "application/json"

    def render(self, content) -> bytes:
        return orjson.dumps(content)


load_dotenv()

# Verificar se a variável de ambiente está sendo carregada
BACKEND_URL = os.getenv("BACKEND_URL")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

logger.info(f"BACKEND_URL: {BACKEND_URL}")
logger.info(f"REDIS_HOST: {REDIS_HOST}")
logger.info(f"REDIS_PORT: {REDIS_PORT}")

# Configurar Redis
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Inicializar repositórios
eleicao_repo = EleicaoRepository(redis_client)
cargo_repo = CargoRepository(redis_client)
candidato_repo = CandidatoRepository(redis_client)
voto_repo = VotoRepository(redis_client)

# Configurar Jinja2 templates
templates = Jinja2Templates(directory="backend/templates")
app = FastAPI(
    templates=templates,
    default_response_class=ORJSONResponse,
    title="Sistema de Votação Eletrônica",
    version="2.0.0"
)

# Configurar CORS para permitir solicitações do frontend
origins = [
    "http://localhost",
    "http://localhost:7000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Adicionar compressão GZIP para respostas > 1KB
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Montar o diretório de arquivos estáticos
app.mount("/static", StaticFiles(directory="backend/static"), name="static")

# Diretório para salvar os arquivos de chave
UPLOAD_DIRECTORY = "uploaded_keys"

if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

# Instância global do sistema de votação
sistema_votacao: Optional[SistemaVotacao] = None
qr_code_service = QRCodeService()

# Métricas de performance
metrics = {
    'total_votos': 0,
    'total_requests': 0,
    'total_errors': 0,
    'start_time': time.time(),
    'request_times': []
}


# Middleware para contabilizar métricas
@app.middleware("http")
async def add_metrics(request: Request, call_next):
    start_time = time.time()
    metrics['total_requests'] += 1

    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        metrics['request_times'].append(process_time)

        # Manter apenas os últimos 1000 tempos
        if len(metrics['request_times']) > 1000:
            metrics['request_times'] = metrics['request_times'][-1000:]

        response.headers["X-Process-Time"] = str(process_time)
        return response
    except Exception as e:
        metrics['total_errors'] += 1
        raise e


@app.get("/", include_in_schema=False)
async def get_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "BACKEND_URL": BACKEND_URL})


@app.get("/urna.html", include_in_schema=False)
async def get_urna(request: Request):
    return templates.TemplateResponse("urna.html", {"request": request, "BACKEND_URL": BACKEND_URL})


@app.get("/escrutinio.html", include_in_schema=False)
async def get_escrutinio(request: Request):
    return templates.TemplateResponse("escrutinio.html", {"request": request, "BACKEND_URL": BACKEND_URL})


@app.post("/upload-keys")
async def upload_keys(
        cryptography_key: UploadFile = File(...),
        private_key: UploadFile = File(...),
        election_data: UploadFile = File(...)
):
    global sistema_votacao
    try:
        # Salvar as chaves de segurança
        cryptography_key_path = os.path.join(UPLOAD_DIRECTORY, "cryptography_key.pem")
        private_key_path = os.path.join(UPLOAD_DIRECTORY, "private_key.pem")

        with open(cryptography_key_path, "wb") as f:
            f.write(await cryptography_key.read())

        with open(private_key_path, "wb") as f:
            f.write(await private_key.read())

        # Processar o arquivo JSON da eleição
        contents = await election_data.read()
        data = orjson.loads(contents)

        # Inicializar os dados da eleição
        eleicao = Eleicao(**data['eleicao'])
        partidos = [Partido(**partido) for partido in data['partidos']]
        cargos = [Cargo(**cargo) for cargo in data['cargos']]
        candidatos = [Candidato(**candidato) for candidato in data['candidatos']]

        # Salvar os dados usando repositórios
        eleicao_repo.save(eleicao.id, json.loads(eleicao.json()))

        for partido in partidos:
            redis_client.set(f"partido:{partido.numero}", partido.json())

        for cargo in cargos:
            cargo_repo.save_with_index(cargo.id, json.loads(cargo.json()))

        for candidato in candidatos:
            candidato_repo.save_with_index(candidato.id, json.loads(candidato.json()))

        # Limpar cache após upload
        invalidate_cache('candidatos')
        invalidate_cache('cargos')

        # Inicializar o sistema de votação
        sistema_votacao = SistemaVotacao(private_key_path, cryptography_key_path)
        logger.info("Sistema de votação inicializado com sucesso!")

        return {"message": "Chaves e dados da eleição enviados com sucesso!"}
    except Exception as e:
        logger.error(f"Erro ao fazer upload das chaves: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/keys-status")
async def keys_status():
    cryptography_key_path = os.path.join(UPLOAD_DIRECTORY, "cryptography_key.pem")
    private_key_path = os.path.join(UPLOAD_DIRECTORY, "private_key.pem")

    keys_exist = os.path.exists(cryptography_key_path) and os.path.exists(private_key_path)
    return {"keys_exist": keys_exist}


@app.get("/cargos/{eleicao_id}")
@cached(key_prefix="cargos", ttl=300)
async def listar_cargos(
        eleicao_id: int,
        skip: int = Query(0, ge=0, description="Número de registros a pular"),
        limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros")
):
    """
    Lista cargos de uma eleição com paginação.
    """
    try:
        result = cargo_repo.get_by_eleicao(eleicao_id, skip=skip, limit=limit)
        return result
    except Exception as e:
        logger.error(f"Erro ao listar cargos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/candidatos/{cargo_id}")
@cached(key_prefix="candidatos", ttl=300)
async def listar_candidatos_por_cargo(
        cargo_id: int,
        skip: int = Query(0, ge=0, description="Número de registros a pular"),
        limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros")
):
    """
    Lista candidatos de um cargo com paginação.
    """
    try:
        result = candidato_repo.get_by_cargo(cargo_id, skip=skip, limit=limit)
        return result
    except Exception as e:
        logger.error(f"Erro ao listar candidatos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/buscar-candidatos/{cargo_id}/{codigo}")
async def buscar_candidatos_por_codigo(cargo_id: int, codigo: str):
    """
    Busca candidatos por código.
    """
    try:
        candidatos = candidato_repo.get_by_codigo(cargo_id, codigo)
        return candidatos
    except Exception as e:
        logger.error(f"Erro ao buscar candidatos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/votar")
async def votar(voto_request: VotoRequest):
    global sistema_votacao
    try:
        # Verificar se o sistema foi inicializado
        if sistema_votacao is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sistema de votação não inicializado. Faça o upload das chaves primeiro."
            )

        # Verificar se o candidato existe
        candidato_key = f"candidato:{voto_request.candidato.id}"
        if not redis_client.exists(candidato_key):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidato não encontrado")

        # Registrar o voto
        voto = sistema_votacao.votar(voto_request.candidato)

        # Gerar QR code
        voto_data = {
            "id": voto.id,
            "candidato_id": voto.candidato.id,
            "candidato_nome": voto.candidato.nome,
            "hash_blockchain": voto.hash_blockchain,
            "hash_localizacao": voto.hash_localizacao,
            "data_hora": voto.data_hora.isoformat() if hasattr(voto.data_hora, 'isoformat') else str(voto.data_hora)
        }
        qr_code_base64 = qr_code_service.gerar_qr_code(orjson.dumps(voto_data).decode('utf-8'))
        voto.qr_code = f"data:image/png;base64,{qr_code_base64}"

        # Salvar usando repositório
        voto_repo.add_voto(voto_request.candidato.eleicao.id, voto.json())

        # Atualizar métricas
        metrics['total_votos'] += 1

        logger.info(f"Voto registrado: ID={voto.id}, Candidato={voto.candidato.nome}")

        return {
            "message": "Voto registrado com sucesso!",
            "voto": json.loads(voto.json())
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao registrar voto: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao registrar voto: {str(e)}")


@app.post("/verificar-voto")
async def verificar_voto(qr_code_data: dict):
    """Verifica um voto através dos dados do QR code"""
    global sistema_votacao
    try:
        if sistema_votacao is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sistema de votação não inicializado."
            )

        voto_id = qr_code_data.get("id")
        hash_blockchain = qr_code_data.get("hash_blockchain")

        if not voto_id or not hash_blockchain:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dados do QR code inválidos."
            )

        # Usar método otimizado de busca por hash
        block = sistema_votacao.blockchain.get_block_by_hash(hash_blockchain)
        found = block is not None

        if found:
            logger.info(f"Voto {voto_id} verificado com sucesso!")
            return {
                "valido": True,
                "message": "Voto verificado com sucesso!",
                "voto_id": voto_id
            }
        else:
            logger.warning(f"Voto {voto_id} não encontrado na blockchain!")
            return {
                "valido": False,
                "message": "Voto não encontrado na blockchain.",
                "voto_id": voto_id
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao verificar voto: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/totalizar-votos/{eleicao_id}")
async def totalizar_votos(eleicao_id: int):
    global sistema_votacao
    try:
        if sistema_votacao is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sistema de votação não inicializado."
            )

        totalizacao = sistema_votacao.totalizar_votos()
        logger.info(f"Totalização de votos realizada para eleição {eleicao_id}")

        return json.loads(totalizacao.json())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao totalizar votos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/gerar-boletim-urna")
async def gerar_boletim_urna():
    """Gera o Boletim de Urna"""
    global sistema_votacao
    try:
        if sistema_votacao is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sistema de votação não inicializado."
            )

        boletim = sistema_votacao.gerar_boletim_urna()
        logger.info(f"Boletim de Urna gerado: ID={boletim.id}")

        return json.loads(boletim.json())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao gerar boletim de urna: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# === ENDPOINTS DE MONITORAMENTO ===

@app.get("/health")
async def health_check():
    """
    Endpoint de health check.
    """
    try:
        # Verificar conexão com Redis
        redis_client.ping()
        redis_status = "healthy"
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if redis_status == "healthy" else "degraded",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "redis": redis_status,
            "sistema_votacao": "initialized" if sistema_votacao else "not_initialized"
        }
    }


@app.get("/metrics")
async def get_metrics():
    """
    Endpoint de métricas do sistema.
    """
    uptime = time.time() - metrics['start_time']
    avg_response_time = (
        sum(metrics['request_times']) / len(metrics['request_times'])
        if metrics['request_times'] else 0
    )

    cache_stats = get_cache_stats()

    blockchain_stats = {}
    if sistema_votacao:
        blockchain_stats = sistema_votacao.blockchain.get_chain_stats()

    return {
        "system": {
            "uptime_seconds": round(uptime, 2),
            "total_requests": metrics['total_requests'],
            "total_errors": metrics['total_errors'],
            "error_rate": round(
                metrics['total_errors'] / metrics['total_requests'] * 100, 2
            ) if metrics['total_requests'] > 0 else 0,
            "avg_response_time_ms": round(avg_response_time * 1000, 2),
        },
        "voting": {
            "total_votos": metrics['total_votos'],
            "votos_per_second": round(
                metrics['total_votos'] / uptime, 2
            ) if uptime > 0 else 0,
        },
        "cache": cache_stats,
        "blockchain": blockchain_stats,
        "redis": {
            "total_keys": redis_client.dbsize(),
        }
    }


@app.get("/cache/stats")
async def cache_stats():
    """
    Estatísticas detalhadas do cache.
    """
    return get_cache_stats()


@app.post("/cache/clear")
async def clear_cache_endpoint():
    """
    Limpa o cache do sistema.
    """
    from core.utils.cache import clear_cache
    clear_cache()
    return {"message": "Cache limpo com sucesso"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
