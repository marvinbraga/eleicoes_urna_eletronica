"""
Configurações de fixtures para os testes do sistema de votação
"""
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Generator

import pytest
from fakeredis import FakeRedis
from fastapi.testclient import TestClient

from core.models.classes import Candidato, Partido, Cargo, Eleicao
from core.processors.classes import SistemaVotacao
from core.utils.security import KeyManager, CryptographyKeyManager


@pytest.fixture(scope="function")
def temp_dir() -> Generator[Path, None, None]:
    """Cria um diretório temporário para os testes"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(scope="function")
def chaves_criptografia(temp_dir: Path) -> dict:
    """Gera chaves de criptografia para os testes"""
    private_key_path = temp_dir / "private_key.pem"
    cryptography_key_path = temp_dir / "cryptography_key.pem"

    # Gera e salva a chave privada
    key_manager = KeyManager(private_key_path=private_key_path.as_posix())
    key_manager.generate_private_key()
    key_manager.save_private_key()

    # Gera e salva a chave de criptografia
    crypto_manager = CryptographyKeyManager(key_path=cryptography_key_path.as_posix())
    crypto_manager.generate_key()
    crypto_manager.save_key()

    return {
        "private_key_path": private_key_path.as_posix(),
        "cryptography_key_path": cryptography_key_path.as_posix()
    }


@pytest.fixture
def fake_redis():
    """Cria uma instância do FakeRedis para testes"""
    redis_client = FakeRedis(decode_responses=True)
    yield redis_client
    redis_client.flushall()


@pytest.fixture
def partido_exemplo() -> Partido:
    """Retorna um partido de exemplo"""
    return Partido(numero=45, sigla="PA", nome="Partido A")


@pytest.fixture
def partido_exemplo_2() -> Partido:
    """Retorna um segundo partido de exemplo"""
    return Partido(numero=65, sigla="PB", nome="Partido B")


@pytest.fixture
def eleicao_exemplo() -> Eleicao:
    """Retorna uma eleição de exemplo"""
    return Eleicao(
        id=1,
        nome="Eleição Municipal 2024",
        data=datetime(2024, 10, 6),
        turnos=1
    )


@pytest.fixture
def cargo_prefeito(eleicao_exemplo: Eleicao) -> Cargo:
    """Retorna um cargo de prefeito"""
    return Cargo(id=1, nome="Prefeito", eleicao=eleicao_exemplo.id)


@pytest.fixture
def cargo_vereador(eleicao_exemplo: Eleicao) -> Cargo:
    """Retorna um cargo de vereador"""
    return Cargo(id=2, nome="Vereador", eleicao=eleicao_exemplo.id)


@pytest.fixture
def candidato_prefeito(partido_exemplo: Partido, cargo_prefeito: Cargo, eleicao_exemplo: Eleicao) -> Candidato:
    """Retorna um candidato a prefeito"""
    return Candidato(
        id=1,
        nome="Candidato 1",
        partido=partido_exemplo,
        codigo="45123",
        foto="foto1.jpg",
        cargo=cargo_prefeito,
        eleicao=eleicao_exemplo
    )


@pytest.fixture
def candidato_vereador(partido_exemplo_2: Partido, cargo_vereador: Cargo, eleicao_exemplo: Eleicao) -> Candidato:
    """Retorna um candidato a vereador"""
    return Candidato(
        id=2,
        nome="Candidato 2",
        partido=partido_exemplo_2,
        codigo="65456",
        foto="foto2.jpg",
        cargo=cargo_vereador,
        eleicao=eleicao_exemplo
    )


@pytest.fixture
def sistema_votacao(chaves_criptografia: dict) -> SistemaVotacao:
    """Cria uma instância do sistema de votação para testes"""
    return SistemaVotacao(
        chave_privada_path=chaves_criptografia["private_key_path"],
        chave_criptografia_path=chaves_criptografia["cryptography_key_path"]
    )


@pytest.fixture
def dados_eleicao_completos(
    eleicao_exemplo: Eleicao,
    partido_exemplo: Partido,
    partido_exemplo_2: Partido,
    cargo_prefeito: Cargo,
    cargo_vereador: Cargo,
    candidato_prefeito: Candidato,
    candidato_vereador: Candidato
) -> dict:
    """Retorna dados completos de uma eleição para testes da API"""
    return {
        "eleicao": eleicao_exemplo.dict(),
        "partidos": [partido_exemplo.dict(), partido_exemplo_2.dict()],
        "cargos": [cargo_prefeito.dict(), cargo_vereador.dict()],
        "candidatos": [candidato_prefeito.dict(), candidato_vereador.dict()]
    }


@pytest.fixture
def mock_redis_with_data(
    fake_redis,
    eleicao_exemplo: Eleicao,
    partido_exemplo: Partido,
    partido_exemplo_2: Partido,
    cargo_prefeito: Cargo,
    cargo_vereador: Cargo,
    candidato_prefeito: Candidato,
    candidato_vereador: Candidato
):
    """Cria um FakeRedis com dados pré-carregados"""
    # Salvar eleição
    fake_redis.set(f"eleicao:{eleicao_exemplo.id}", eleicao_exemplo.json())

    # Salvar partidos
    fake_redis.set(f"partido:{partido_exemplo.numero}", partido_exemplo.json())
    fake_redis.set(f"partido:{partido_exemplo_2.numero}", partido_exemplo_2.json())

    # Salvar cargos
    fake_redis.set(f"cargo:{cargo_prefeito.id}", cargo_prefeito.json())
    fake_redis.set(f"cargo:{cargo_vereador.id}", cargo_vereador.json())

    # Salvar candidatos
    fake_redis.set(f"candidato:{candidato_prefeito.id}", candidato_prefeito.json())
    fake_redis.set(f"candidato:{candidato_vereador.id}", candidato_vereador.json())

    return fake_redis


@pytest.fixture
def client(mocker, mock_redis_with_data, chaves_criptografia, temp_dir):
    """Cria um cliente de teste para a API FastAPI"""
    # Mock das variáveis de ambiente antes de importar
    mocker.patch.dict(os.environ, {
        "BACKEND_URL": "http://localhost:8000",
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "6379"
    })

    # Importa o módulo backend.app
    import backend.app as app_module

    # Mock do Redis após importar
    mocker.patch.object(app_module, "redis_client", mock_redis_with_data)

    # Cria diretório para upload de chaves
    upload_dir = temp_dir / "uploaded_keys"
    upload_dir.mkdir(exist_ok=True)
    mocker.patch.object(app_module, "UPLOAD_DIRECTORY", str(upload_dir))

    return TestClient(app_module.app)


@pytest.fixture
def client_with_sistema_inicializado(client, chaves_criptografia, mocker):
    """Cria um cliente com sistema de votação já inicializado"""
    import backend.app as app_module

    # Inicializa o sistema de votação
    sistema = SistemaVotacao(
        chave_privada_path=chaves_criptografia["private_key_path"],
        chave_criptografia_path=chaves_criptografia["cryptography_key_path"]
    )

    # Mock da variável global sistema_votacao
    mocker.patch.object(app_module, "sistema_votacao", sistema)

    return client


@pytest.fixture
def arquivos_upload(chaves_criptografia: dict, dados_eleicao_completos: dict, temp_dir: Path):
    """Cria arquivos para upload nos testes de API"""
    # Cria arquivos temporários para upload
    with open(chaves_criptografia["private_key_path"], "rb") as f:
        private_key_content = f.read()

    with open(chaves_criptografia["cryptography_key_path"], "rb") as f:
        cryptography_key_content = f.read()

    election_data = json.dumps(dados_eleicao_completos).encode()

    return {
        "private_key": ("private_key.pem", private_key_content, "application/x-pem-file"),
        "cryptography_key": ("cryptography_key.pem", cryptography_key_content, "application/x-pem-file"),
        "election_data": ("election_data.json", election_data, "application/json")
    }


@pytest.fixture(autouse=True)
def limpar_logs_auditoria():
    """Limpa os arquivos de log de auditoria após cada teste"""
    yield
    # Limpa logs de auditoria criados durante os testes
    security_dir = Path("/home/user/eleicoes_urna_eletronica/security")
    if security_dir.exists():
        for log_file in security_dir.glob("audit_*.log"):
            try:
                log_file.unlink()
            except Exception:
                pass
