"""
Testes para o serviço de boletim de urna
"""
import base64
import json
import pytest

from core.processors.classes import (
    BoletimUrnaService, VotoService, CriptografiaService,
    IntegrityVerifier, NonceGenerator, AuditLogger
)
from core.blockchain.classes import Blockchain
from core.utils.datetime import datetime_to_string


@pytest.mark.unit
class TestBoletimUrnaService:
    """Testes para o serviço de boletim de urna"""

    @pytest.fixture
    def voto_service(self, chaves_criptografia):
        """Cria uma instância do serviço de votação"""
        cripto_service = CriptografiaService(
            chave_privada_path=chaves_criptografia["private_key_path"],
            chave_criptografia_path=chaves_criptografia["cryptography_key_path"]
        )
        blockchain = Blockchain()
        integrity_verifier = IntegrityVerifier()
        nonce_generator = NonceGenerator()
        audit_logger = AuditLogger()

        return VotoService(
            cripto_service,
            blockchain,
            integrity_verifier,
            nonce_generator,
            audit_logger
        )

    @pytest.fixture
    def boletim_service(self, chaves_criptografia, voto_service):
        """Cria uma instância do serviço de boletim de urna"""
        cripto_service = CriptografiaService(
            chave_privada_path=chaves_criptografia["private_key_path"],
            chave_criptografia_path=chaves_criptografia["cryptography_key_path"]
        )

        return BoletimUrnaService(cripto_service, voto_service)

    def test_inicializacao_servico(self, boletim_service):
        """Testa se o serviço é inicializado corretamente"""
        assert boletim_service.criptografia_service is not None
        assert boletim_service.voto_service is not None
        assert len(boletim_service.boletins_urna) == 0

    def test_gerar_boletim_urna(self, boletim_service, voto_service, candidato_prefeito):
        """Testa a geração de um boletim de urna"""
        # Registra alguns votos
        voto_service.votar(candidato_prefeito)

        # Gera o boletim
        boletim = boletim_service.gerar_boletim_urna()

        assert boletim is not None
        assert boletim.id == 1
        assert boletim.secao is not None
        assert boletim.zona is not None
        assert len(boletim.votos) == 1
        assert boletim.assinatura is not None

    def test_gerar_multiplos_boletins(self, boletim_service, voto_service, candidato_prefeito):
        """Testa a geração de múltiplos boletins"""
        voto_service.votar(candidato_prefeito)

        boletim1 = boletim_service.gerar_boletim_urna()
        boletim2 = boletim_service.gerar_boletim_urna()

        assert boletim1.id == 1
        assert boletim2.id == 2
        assert len(boletim_service.boletins_urna) == 2

    def test_boletim_contem_hash_blockchain(self, boletim_service, voto_service, candidato_prefeito):
        """Testa que o boletim contém o hash final da blockchain"""
        voto_service.votar(candidato_prefeito)
        boletim = boletim_service.gerar_boletim_urna()

        hash_final_blockchain = voto_service.blockchain.chain[-1].hash
        assert boletim.hash_final_blockchain == hash_final_blockchain
        assert boletim.hash_bu == hash_final_blockchain

    def test_boletim_contem_votos(self, boletim_service, voto_service, candidato_prefeito, candidato_vereador):
        """Testa que o boletim contém todos os votos registrados"""
        voto1 = voto_service.votar(candidato_prefeito)
        voto2 = voto_service.votar(candidato_vereador)

        boletim = boletim_service.gerar_boletim_urna()

        assert len(boletim.votos) == 2
        assert voto1 in boletim.votos
        assert voto2 in boletim.votos

    def test_boletim_assinado_digitalmente(self, boletim_service, voto_service, candidato_prefeito):
        """Testa que o boletim é assinado digitalmente"""
        voto_service.votar(candidato_prefeito)
        boletim = boletim_service.gerar_boletim_urna()

        assert boletim.assinatura is not None
        assert len(boletim.assinatura) > 0

        # Verifica que a assinatura é válida
        boletim_dict = boletim.dict(exclude_none=True, exclude={'assinatura'})
        assinatura = base64.b64decode(boletim.assinatura)

        resultado = boletim_service.criptografia_service.verificar_assinatura(
            json.dumps(boletim_dict, default=datetime_to_string, sort_keys=True),
            assinatura
        )
        assert resultado is True

    def test_validar_boletim_urna_valido(self, boletim_service, voto_service, candidato_prefeito):
        """Testa a validação de um boletim de urna válido"""
        voto_service.votar(candidato_prefeito)
        boletim = boletim_service.gerar_boletim_urna()

        # Valida o boletim
        resultado = boletim_service.validar_boletim_urna(boletim)
        assert resultado is True

    def test_validar_boletim_urna_inexistente(self, boletim_service, voto_service, candidato_prefeito):
        """Testa a validação de um boletim inexistente"""
        voto_service.votar(candidato_prefeito)
        boletim_real = boletim_service.gerar_boletim_urna()

        # Cria um boletim falso
        from core.models.classes import BoletimUrna
        from datetime import datetime

        boletim_falso = BoletimUrna(
            id=999,
            secao="Seção Falsa",
            zona="Zona Falsa",
            municipio="Município Falso",
            estado="Estado Falso",
            data_hora=datetime.now(),
            hash_final_blockchain="hash_falso",
            hash_bu="hash_falso",
            qr_code="qr_falso",
            votos=[],
            assinatura="assinatura_falsa"
        )

        resultado = boletim_service.validar_boletim_urna(boletim_falso)
        assert resultado is False

    def test_validar_boletim_assinatura_modificada(self, boletim_service, voto_service, candidato_prefeito):
        """Testa que boletim com assinatura modificada é invalidado"""
        voto_service.votar(candidato_prefeito)
        boletim = boletim_service.gerar_boletim_urna()

        # Modifica a assinatura
        boletim.assinatura = base64.b64encode(b"assinatura_modificada").decode()

        resultado = boletim_service.validar_boletim_urna(boletim)
        assert resultado is False

    def test_boletim_sem_votos(self, boletim_service):
        """Testa a geração de boletim sem votos"""
        boletim = boletim_service.gerar_boletim_urna()

        assert boletim is not None
        assert len(boletim.votos) == 0
        assert boletim.assinatura is not None

    def test_boletim_com_muitos_votos(self, boletim_service, voto_service, candidato_prefeito):
        """Testa a geração de boletim com muitos votos"""
        # Registra 100 votos
        for i in range(100):
            voto_service.votar(candidato_prefeito)

        boletim = boletim_service.gerar_boletim_urna()

        assert len(boletim.votos) == 100
        assert boletim.assinatura is not None

    def test_boletim_qr_code_gerado(self, boletim_service, voto_service, candidato_prefeito):
        """Testa que o boletim contém um QR code"""
        voto_service.votar(candidato_prefeito)
        boletim = boletim_service.gerar_boletim_urna()

        assert boletim.qr_code is not None
        assert len(boletim.qr_code) > 0

    def test_boletim_contem_dados_localizacao(self, boletim_service, voto_service, candidato_prefeito):
        """Testa que o boletim contém dados de localização da urna"""
        voto_service.votar(candidato_prefeito)
        boletim = boletim_service.gerar_boletim_urna()

        assert boletim.secao is not None
        assert boletim.zona is not None
        assert boletim.municipio is not None
        assert boletim.estado is not None

    @pytest.mark.parametrize("num_votos", [0, 1, 5, 10, 50])
    def test_gerar_boletim_com_diferentes_quantidades_votos(
        self, boletim_service, voto_service, candidato_prefeito, num_votos
    ):
        """Testa a geração de boletim com diferentes quantidades de votos"""
        for i in range(num_votos):
            voto_service.votar(candidato_prefeito)

        boletim = boletim_service.gerar_boletim_urna()

        assert len(boletim.votos) == num_votos
        assert boletim_service.validar_boletim_urna(boletim) is True
