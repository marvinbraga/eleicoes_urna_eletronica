import json
import os

import redis
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger

from core.models.classes import Eleicao, Partido, Cargo, Candidato

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
async def upload_keys(cryptography_key: UploadFile = File(...), private_key: UploadFile = File(...)):
    try:
        cryptography_key_path = os.path.join(UPLOAD_DIRECTORY, cryptography_key.filename)
        private_key_path = os.path.join(UPLOAD_DIRECTORY, private_key.filename)

        with open(cryptography_key_path, "wb") as f:
            f.write(await cryptography_key.read())

        with open(private_key_path, "wb") as f:
            f.write(await private_key.read())

        return JSONResponse(content={"message": "Chaves enviadas com sucesso!"}, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/keys-status")
async def keys_status():
    cryptography_key_path = os.path.join(UPLOAD_DIRECTORY, "cryptography_key.pem")
    private_key_path = os.path.join(UPLOAD_DIRECTORY, "private_key.pem")

    keys_exist = os.path.exists(cryptography_key_path) and os.path.exists(private_key_path)
    return JSONResponse(content={"keys_exist": keys_exist}, status_code=200)


# Endpoints para cadastrar dados
@app.post("/eleicao")
async def create_eleicao(eleicao: Eleicao):
    # Salvar a eleição no Redis
    redis_client.set(f"eleicao:{eleicao.id}", eleicao.json())
    return eleicao


@app.post("/partido")
async def create_partido(partido: Partido):
    # Salvar o partido no Redis
    redis_client.set(f"partido:{partido.numero}", partido.json())
    return partido


@app.post("/cargo")
async def create_cargo(cargo: Cargo):
    # Salvar o cargo no Redis
    redis_client.set(f"cargo:{cargo.id}", cargo.json())
    return cargo


@app.post("/candidato")
async def create_candidato(candidato: Candidato):
    # Salvar o candidato no Redis
    redis_client.set(f"candidato:{candidato.id}", candidato.json())
    return candidato


@app.get("/test-redis")
async def test_redis():
    try:
        redis_client.set("test_key", "test_value")
        value = redis_client.get("test_key")
        return JSONResponse(content={"test_key": value}, status_code=200)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload-eleicao")
async def upload_eleicao(file: UploadFile = File(...)):
    try:
        # Ler o conteúdo do arquivo JSON
        contents = await file.read()
        data = json.loads(contents)

        # Processar os dados do JSON e inicializar a urna
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

        return JSONResponse(content={"message": "Dados da eleição enviados e processados com sucesso!"},
                            status_code=200)
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
