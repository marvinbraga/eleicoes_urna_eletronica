import os

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
logger.info(f"BACKEND_URL: {BACKEND_URL}")

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


# Endpoints para cadastrar dados
@app.post("/eleicao")
async def create_eleicao(eleicao: Eleicao):
    # Lógica para salvar a eleição no banco de dados
    return eleicao


@app.post("/partido")
async def create_partido(partido: Partido):
    # Lógica para salvar o partido no banco de dados
    return partido


@app.post("/cargo")
async def create_cargo(cargo: Cargo):
    # Lógica para salvar o cargo no banco de dados
    return cargo


@app.post("/candidato")
async def create_candidato(candidato: Candidato):
    # Lógica para salvar o candidato no banco de dados
    return candidato
