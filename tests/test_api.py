"""
Testes para a API REST do sistema de votação eletrônica
"""
import json
import pytest
from fastapi import status
from unittest.mock import MagicMock


@pytest.mark.unit
class TestIndexEndpoints:
    """Testes para endpoints de páginas HTML"""

    def test_get_index(self, client):
        """Testa o endpoint raiz (index.html)"""
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK

    def test_get_urna(self, client):
        """Testa o endpoint da urna (urna.html)"""
        response = client.get("/urna.html")
        assert response.status_code == status.HTTP_200_OK

    def test_get_escrutinio(self, client):
        """Testa o endpoint de escrutínio (escrutinio.html)"""
        response = client.get("/escrutinio.html")
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.unit
class TestKeysEndpoints:
    """Testes para endpoints relacionados a chaves criptográficas"""

    def test_keys_status_sem_chaves(self, client):
        """Testa o status das chaves quando não há chaves carregadas"""
        response = client.get("/keys-status")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "keys_exist" in data
        assert isinstance(data["keys_exist"], bool)

    def test_upload_keys_sucesso(self, client, arquivos_upload):
        """Testa o upload de chaves e dados da eleição com sucesso"""
        files = {
            "private_key": arquivos_upload["private_key"],
            "cryptography_key": arquivos_upload["cryptography_key"],
            "election_data": arquivos_upload["election_data"]
        }

        response = client.post("/upload-keys", files=files)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "sucesso" in data["message"].lower()

    def test_upload_keys_arquivo_invalido(self, client):
        """Testa o upload de chaves com arquivo inválido"""
        files = {
            "private_key": ("private_key.pem", b"invalid", "application/x-pem-file"),
            "cryptography_key": ("cryptography_key.pem", b"invalid", "application/x-pem-file"),
            "election_data": ("election_data.json", b"invalid json", "application/json")
        }

        response = client.post("/upload-keys", files=files)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.unit
class TestCargosEndpoints:
    """Testes para endpoints relacionados a cargos"""

    def test_listar_cargos_sucesso(self, client):
        """Testa a listagem de cargos para uma eleição"""
        response = client.get("/cargos/1")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_listar_cargos_eleicao_sem_cargos(self, client):
        """Testa a listagem de cargos para uma eleição sem cargos cadastrados"""
        response = client.get("/cargos/999")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0


@pytest.mark.unit
class TestCandidatosEndpoints:
    """Testes para endpoints relacionados a candidatos"""

    def test_listar_candidatos_por_cargo(self, client):
        """Testa a listagem de candidatos por cargo"""
        response = client.get("/candidatos/1")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_listar_candidatos_cargo_sem_candidatos(self, client):
        """Testa a listagem de candidatos para um cargo sem candidatos"""
        response = client.get("/candidatos/999")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_buscar_candidatos_por_codigo(self, client):
        """Testa a busca de candidatos por código"""
        response = client.get("/buscar-candidatos/1/45")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_buscar_candidatos_codigo_inexistente(self, client):
        """Testa a busca de candidatos com código inexistente"""
        response = client.get("/buscar-candidatos/1/99")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0


@pytest.mark.unit
class TestVotacaoEndpoints:
    """Testes para endpoints relacionados à votação"""

    def test_votar_sistema_nao_inicializado(self, client, candidato_prefeito):
        """Testa votação quando o sistema não está inicializado"""
        voto_data = {
            "candidato": candidato_prefeito.dict()
        }

        response = client.post("/votar", json=voto_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "detail" in data
        assert "não inicializado" in data["detail"].lower()

    def test_votar_sucesso(self, client_with_sistema_inicializado, candidato_prefeito, mocker):
        """Testa votação bem-sucedida"""
        # Mock do redis.exists para retornar True
        mocker.patch("backend.app.redis_client.exists", return_value=True)

        voto_data = {
            "candidato": candidato_prefeito.dict()
        }

        response = client_with_sistema_inicializado.post("/votar", json=voto_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "voto" in data
        assert data["voto"]["candidato"]["id"] == candidato_prefeito.id

    def test_votar_candidato_nao_encontrado(self, client_with_sistema_inicializado, candidato_prefeito, mocker):
        """Testa votação com candidato não encontrado"""
        # Mock do redis.exists para retornar False
        mocker.patch("backend.app.redis_client.exists", return_value=False)

        voto_data = {
            "candidato": candidato_prefeito.dict()
        }

        response = client_with_sistema_inicializado.post("/votar", json=voto_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.unit
class TestVerificacaoVotoEndpoints:
    """Testes para endpoints de verificação de voto"""

    def test_verificar_voto_sistema_nao_inicializado(self, client):
        """Testa verificação de voto quando sistema não está inicializado"""
        qr_data = {
            "id": 1,
            "hash_blockchain": "abc123"
        }

        response = client.post("/verificar-voto", json=qr_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_verificar_voto_dados_invalidos(self, client_with_sistema_inicializado):
        """Testa verificação de voto com dados inválidos"""
        qr_data = {
            "id": 1
            # Falta hash_blockchain
        }

        response = client_with_sistema_inicializado.post("/verificar-voto", json=qr_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_verificar_voto_nao_encontrado(self, client_with_sistema_inicializado):
        """Testa verificação de voto não encontrado na blockchain"""
        qr_data = {
            "id": 1,
            "hash_blockchain": "hash_inexistente"
        }

        response = client_with_sistema_inicializado.post("/verificar-voto", json=qr_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["valido"] is False

    def test_verificar_voto_encontrado(self, client_with_sistema_inicializado, candidato_prefeito, mocker):
        """Testa verificação de voto encontrado na blockchain"""
        # Primeiro registra um voto
        mocker.patch("backend.app.redis_client.exists", return_value=True)
        mocker.patch("backend.app.redis_client.rpush", return_value=1)

        voto_data = {
            "candidato": candidato_prefeito.dict()
        }

        response = client_with_sistema_inicializado.post("/votar", json=voto_data)
        assert response.status_code == status.HTTP_200_OK

        # Pega o hash do voto registrado
        from backend import app as backend_app
        hash_blockchain = backend_app.sistema_votacao.blockchain.chain[-1].hash

        # Verifica o voto
        qr_data = {
            "id": 1,
            "hash_blockchain": hash_blockchain
        }

        response = client_with_sistema_inicializado.post("/verificar-voto", json=qr_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["valido"] is True


@pytest.mark.unit
class TestTotalizacaoEndpoints:
    """Testes para endpoints de totalização"""

    def test_totalizar_votos_sistema_nao_inicializado(self, client):
        """Testa totalização quando sistema não está inicializado"""
        response = client.get("/totalizar-votos/1")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_totalizar_votos_sucesso(self, client_with_sistema_inicializado):
        """Testa totalização de votos com sucesso"""
        response = client_with_sistema_inicializado.get("/totalizar-votos/1")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "id" in data
        assert "votos_totalizados" in data
        assert "assinatura" in data


@pytest.mark.unit
class TestBoletimUrnaEndpoints:
    """Testes para endpoints de boletim de urna"""

    def test_gerar_boletim_urna_sistema_nao_inicializado(self, client):
        """Testa geração de boletim quando sistema não está inicializado"""
        response = client.get("/gerar-boletim-urna")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_gerar_boletim_urna_sucesso(self, client_with_sistema_inicializado):
        """Testa geração de boletim de urna com sucesso"""
        response = client_with_sistema_inicializado.get("/gerar-boletim-urna")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "id" in data
        assert "secao" in data
        assert "zona" in data
        assert "votos" in data
        assert "assinatura" in data


@pytest.mark.integration
class TestFluxoCompleto:
    """Testes de fluxo completo da API"""

    def test_fluxo_votacao_completo(self, client, arquivos_upload, candidato_prefeito, mocker):
        """
        Testa o fluxo completo de votação:
        1. Upload de chaves
        2. Votação
        3. Verificação de voto
        4. Geração de boletim
        5. Totalização
        """
        # 1. Upload de chaves
        files = {
            "private_key": arquivos_upload["private_key"],
            "cryptography_key": arquivos_upload["cryptography_key"],
            "election_data": arquivos_upload["election_data"]
        }

        response = client.post("/upload-keys", files=files)
        assert response.status_code == status.HTTP_200_OK

        # Mock necessário para votação
        mocker.patch("backend.app.redis_client.exists", return_value=True)
        mocker.patch("backend.app.redis_client.rpush", return_value=1)

        # 2. Votação
        voto_data = {
            "candidato": candidato_prefeito.dict()
        }

        response = client.post("/votar", json=voto_data)
        assert response.status_code == status.HTTP_200_OK
        voto_response = response.json()

        # 3. Verificação de voto
        from backend import app as backend_app
        hash_blockchain = backend_app.sistema_votacao.blockchain.chain[-1].hash

        qr_data = {
            "id": voto_response["voto"]["id"],
            "hash_blockchain": hash_blockchain
        }

        response = client.post("/verificar-voto", json=qr_data)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["valido"] is True

        # 4. Geração de boletim
        response = client.get("/gerar-boletim-urna")
        assert response.status_code == status.HTTP_200_OK

        # 5. Totalização
        response = client.get("/totalizar-votos/1")
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.unit
@pytest.mark.parametrize("eleicao_id,expected_cargos", [
    (1, 2),  # Eleição 1 tem 2 cargos
    (999, 0),  # Eleição inexistente
])
def test_listar_cargos_parametrizado(client, eleicao_id, expected_cargos):
    """Testa listagem de cargos com diferentes eleições"""
    response = client.get(f"/cargos/{eleicao_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == expected_cargos


@pytest.mark.unit
@pytest.mark.parametrize("cargo_id,codigo_busca,expected_min", [
    (1, "45", 1),  # Cargo 1 com código 45 deve ter pelo menos 1 candidato
    (1, "99", 0),  # Cargo 1 com código 99 não deve ter candidatos
    (999, "45", 0),  # Cargo inexistente
])
def test_buscar_candidatos_parametrizado(client, cargo_id, codigo_busca, expected_min):
    """Testa busca de candidatos com diferentes parâmetros"""
    response = client.get(f"/buscar-candidatos/{cargo_id}/{codigo_busca}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) >= expected_min
