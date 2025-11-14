import json
import os
from datetime import datetime
from typing import Optional

import redis
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger
from pydantic import BaseModel

from core.models.classes import Eleicao, Partido, Cargo, Candidato, Voto, TotalizacaoVotos
from core.processors.classes import SistemaVotacao
from core.utils.qr_code_gen import QRCodeService


# Modelo para receber dados de voto do frontend
class VotoRequest(BaseModel):
    candidato: Candidato


load_dotenv()

# Verificar se a variável de ambiente está sendo carregada
BACKEND_URL = os.getenv("BACKEND_URL")
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")

logger.info(f"BACKEND_URL: {BACKEND_URL}")
logger.info(f"REDIS_HOST: {REDIS_HOST}")
logger.info(f"REDIS_PORT: {REDIS_PORT}")

# Configurar Redis
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Configurar Jinja2 templates
templates = Jinja2Templates(directory="backend/templates")
app = FastAPI(templates=templates)

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

# Montar o diretório de arquivos estáticos
app.mount("/static", StaticFiles(directory="backend/static"), name="static")

# Diretório para salvar os arquivos de chave
UPLOAD_DIRECTORY = "uploaded_keys"

if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

# Instância global do sistema de votação (será inicializada quando as chaves forem carregadas)
sistema_votacao: Optional[SistemaVotacao] = None
qr_code_service = QRCodeService()


@app.get("/")
async def get_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "BACKEND_URL": BACKEND_URL})


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
        data = json.loads(contents)

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
        sistema_votacao = SistemaVotacao(private_key_path, cryptography_key_path)
        logger.info("Sistema de votação inicializado com sucesso!")

        return JSONResponse(content={"message": "Chaves e dados da eleição enviados com sucesso!"}, status_code=200)
    except Exception as e:
        logger.error(f"Erro ao fazer upload das chaves: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/keys-status")
async def keys_status():
    cryptography_key_path = os.path.join(UPLOAD_DIRECTORY, "cryptography_key.pem")
    private_key_path = os.path.join(UPLOAD_DIRECTORY, "private_key.pem")

    keys_exist = os.path.exists(cryptography_key_path) and os.path.exists(private_key_path)
    return JSONResponse(content={"keys_exist": keys_exist}, status_code=200)


@app.get("/cargos/{eleicao_id}")
async def listar_cargos(eleicao_id: int):
    try:
        cargos = []
        for key in redis_client.scan_iter(f"cargo:*"):
            cargo = json.loads(redis_client.get(key))
            logger.info(f"Cargo encontrado: {cargo}")  # Adicionando log para depuração
            if cargo['eleicao'] == eleicao_id:
                cargos.append(cargo)
        logger.info(f"Cargos filtrados: {cargos}")  # Adicionando log para depuração
        return JSONResponse(content=cargos, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/candidatos/{cargo_id}")
async def listar_candidatos_por_cargo(cargo_id: int):
    try:
        candidatos = []
        for key in redis_client.scan_iter(f"candidato:*"):
            candidato = json.loads(redis_client.get(key))
            if candidato['cargo']['id'] == cargo_id:
                candidatos.append(candidato)
        return JSONResponse(content=candidatos, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/buscar-candidatos/{cargo_id}/{codigo}")
async def buscar_candidatos_por_codigo(cargo_id: int, codigo: str):
    try:
        candidatos = []
        for key in redis_client.scan_iter(f"candidato:*"):
            candidato = json.loads(redis_client.get(key))
            if candidato['cargo']['id'] == cargo_id and candidato['codigo'].startswith(codigo):
                candidatos.append(candidato)
        return JSONResponse(content=candidatos, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/votar")
async def votar(voto_request: VotoRequest):
    global sistema_votacao
    try:
        # Verificar se o sistema de votação foi inicializado
        if sistema_votacao is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sistema de votação não inicializado. Faça o upload das chaves primeiro."
            )

        # Verificar se o candidato existe no Redis
        candidato_key = f"candidato:{voto_request.candidato.id}"
        if not redis_client.exists(candidato_key):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidato não encontrado")

        # Registrar o voto usando o sistema de votação
        voto = sistema_votacao.votar(voto_request.candidato)

        # Gerar QR code do voto
        voto_data = {
            "id": voto.id,
            "candidato_id": voto.candidato.id,
            "candidato_nome": voto.candidato.nome,
            "hash_blockchain": voto.hash_blockchain,
            "hash_localizacao": voto.hash_localizacao,
            "data_hora": voto.data_hora.isoformat() if hasattr(voto.data_hora, 'isoformat') else str(voto.data_hora)
        }
        qr_code_base64 = qr_code_service.gerar_qr_code(json.dumps(voto_data))

        # Atualizar o voto com o QR code em base64
        voto.qr_code = f"data:image/png;base64,{qr_code_base64}"

        # Salvar o voto no Redis
        redis_client.rpush(f"votos:{voto_request.candidato.eleicao.id}", voto.json())

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
            if block.hash == hash_blockchain:
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
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/totalizar-votos/{eleicao_id}")
async def totalizar_votos(eleicao_id: int):
    global sistema_votacao
    try:
        # Verificar se o sistema de votação foi inicializado
        if sistema_votacao is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sistema de votação não inicializado."
            )

        # Totalizar votos usando o sistema de votação
        totalizacao = sistema_votacao.totalizar_votos()

        logger.info(f"Totalização de votos realizada para eleição {eleicao_id}")

        return JSONResponse(content=json.loads(totalizacao.json()), status_code=200)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao totalizar votos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/gerar-boletim-urna")
async def gerar_boletim_urna():
    """Gera o Boletim de Urna com todos os votos registrados"""
    global sistema_votacao
    try:
        if sistema_votacao is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sistema de votação não inicializado."
            )

        # Gerar boletim de urna
        boletim = sistema_votacao.gerar_boletim_urna()

        logger.info(f"Boletim de Urna gerado: ID={boletim.id}")

        return JSONResponse(content=json.loads(boletim.json()), status_code=200)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao gerar boletim de urna: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
