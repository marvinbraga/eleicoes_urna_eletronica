import json
import os
from datetime import datetime

import redis
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger

from core.models.classes import Eleicao, Partido, Cargo, Candidato, Voto, TotalizacaoVotos

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


@app.get("/")
async def get_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "BACKEND_URL": BACKEND_URL})


@app.post("/upload-keys")
async def upload_keys(
        cryptography_key: UploadFile = File(...),
        private_key: UploadFile = File(...),
        election_data: UploadFile = File(...)
):
    try:
        # Salvar as chaves de segurança
        cryptography_key_path = os.path.join(UPLOAD_DIRECTORY, cryptography_key.filename)
        private_key_path = os.path.join(UPLOAD_DIRECTORY, private_key.filename)

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

        return JSONResponse(content={"message": "Chaves e dados da eleição enviados com sucesso!"}, status_code=200)
    except Exception as e:
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
async def votar(voto: Voto):
    try:
        # Verificar se o candidato existe
        candidato_key = f"candidato:{voto.candidato.id}"
        if not redis_client.exists(candidato_key):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidato não encontrado")

        # Salvar o voto no Redis
        redis_client.rpush(f"votos:{voto.candidato.eleicao.id}", voto.json())
        return JSONResponse(content={"message": "Voto registrado com sucesso!"}, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/totalizar-votos/{eleicao_id}")
async def totalizar_votos(eleicao_id: int):
    try:
        votos = []
        for voto_json in redis_client.lrange(f"votos:{eleicao_id}", 0, -1):
            voto = Voto.parse_raw(voto_json)
            votos.append(voto)

        totalizacao = TotalizacaoVotos(
            id=eleicao_id,
            data_hora=datetime.now(),
            votos_totalizados=votos,
            hash_blockchain="hash_blockchain_placeholder"
        )

        return JSONResponse(content=totalizacao.dict(), status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cargos/{eleicao_id}")
async def listar_cargos(eleicao_id: int):
    try:
        cargos = []
        for key in redis_client.scan_iter(f"cargo:*"):
            cargo = json.loads(redis_client.get(key))
            if cargo['eleicao'] == eleicao_id:
                cargos.append(cargo)
        return JSONResponse(content=cargos, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
