"""
Testes para o serviço de totalização de votos
"""
import base64
import json
import pytest

from core.processors.classes import (
    TotalizacaoVotosService, VotoService, CriptografiaService,
    IntegrityVerifier, NonceGenerator, AuditLogger
)
from core.blockchain.classes import Blockchain
from core.utils.datetime import datetime_to_string


@pytest.mark.unit
class TestTotalizacaoVotosService:
    """Testes para o serviço de totalização de votos"""

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
    def totalizacao_service(self, chaves_criptografia, voto_service):
        """Cria uma instância do serviço de totalização"""
        cripto_service = CriptografiaService(
            chave_privada_path=chaves_criptografia["private_key_path"],
            chave_criptografia_path=chaves_criptografia["cryptography_key_path"]
        )
        audit_logger = AuditLogger()

        return TotalizacaoVotosService(cripto_service, voto_service, audit_logger)

    def test_inicializacao_servico(self, totalizacao_service):
        """Testa se o serviço é inicializado corretamente"""
        assert totalizacao_service.criptografia_service is not None
        assert totalizacao_service.voto_service is not None
        assert totalizacao_service.audit_logger is not None

    def test_totalizar_votos_sem_votos(self, totalizacao_service):
        """Testa a totalização quando não há votos"""
        totalizacao = totalizacao_service.totalizar_votos()

        assert totalizacao is not None
        assert len(totalizacao.votos_totalizados) == 0
        assert totalizacao.assinatura is not None

    def test_totalizar_votos_um_candidato(self, totalizacao_service, voto_service, candidato_prefeito):
        """Testa a totalização com votos para um único candidato"""
        # Registra 5 votos para o mesmo candidato
        for i in range(5):
            voto_service.votar(candidato_prefeito)

        totalizacao = totalizacao_service.totalizar_votos()

        assert len(totalizacao.votos_totalizados) == 1
        assert totalizacao.votos_totalizados[0].candidato == candidato_prefeito

    def test_totalizar_votos_multiplos_candidatos(
        self, totalizacao_service, voto_service, candidato_prefeito, candidato_vereador
    ):
        """Testa a totalização com votos para múltiplos candidatos"""
        # Registra votos para diferentes candidatos
        voto_service.votar(candidato_prefeito)
        voto_service.votar(candidato_prefeito)
        voto_service.votar(candidato_vereador)

        totalizacao = totalizacao_service.totalizar_votos()

        assert len(totalizacao.votos_totalizados) == 2

    def test_totalizacao_assinada(self, totalizacao_service, voto_service, candidato_prefeito):
        """Testa que a totalização é assinada digitalmente"""
        voto_service.votar(candidato_prefeito)
        totalizacao = totalizacao_service.totalizar_votos()

        assert totalizacao.assinatura is not None
        assert len(totalizacao.assinatura) > 0

    def test_verificar_integridade_totalizacao_valida(
        self, totalizacao_service, voto_service, candidato_prefeito
    ):
        """Testa a verificação de integridade de uma totalização válida"""
        voto_service.votar(candidato_prefeito)
        totalizacao = totalizacao_service.totalizar_votos()

        resultado = totalizacao_service.verificar_integridade_totalizacao(totalizacao)
        assert resultado is True

    def test_verificar_integridade_totalizacao_modificada(
        self, totalizacao_service, voto_service, candidato_prefeito
    ):
        """Testa que totalização modificada é detectada"""
        voto_service.votar(candidato_prefeito)
        totalizacao = totalizacao_service.totalizar_votos()

        # Modifica a totalização
        assinatura_original = totalizacao.assinatura
        totalizacao.assinatura = base64.b64encode(b"assinatura_modificada").decode()

        resultado = totalizacao_service.verificar_integridade_totalizacao(totalizacao)
        assert resultado is False

    def test_totalizacao_contem_hash_blockchain(
        self, totalizacao_service, voto_service, candidato_prefeito
    ):
        """Testa que a totalização contém o hash da blockchain"""
        voto_service.votar(candidato_prefeito)
        totalizacao = totalizacao_service.totalizar_votos()

        hash_blockchain = voto_service.blockchain.chain[-1].hash
        assert totalizacao.hash_blockchain == hash_blockchain

    def test_totalizacao_registrada_auditoria(
        self, totalizacao_service, voto_service, candidato_prefeito, monkeypatch
    ):
        """Testa que a totalização é registrada no log de auditoria"""
        log_chamado = []

        def mock_log(message):
            log_chamado.append(message)

        monkeypatch.setattr(totalizacao_service.audit_logger, "log", mock_log)

        voto_service.votar(candidato_prefeito)
        totalizacao_service.totalizar_votos()

        assert len(log_chamado) > 0
        assert any("Totalização" in msg for msg in log_chamado)

    def test_totalizar_apenas_votos_validos(
        self, totalizacao_service, voto_service, candidato_prefeito
    ):
        """Testa que apenas votos válidos são totalizados"""
        # Registra votos válidos
        voto_service.votar(candidato_prefeito)
        voto_service.votar(candidato_prefeito)

        # Adiciona uma transação inválida diretamente na blockchain
        voto_service.blockchain.add_transaction("transacao_invalida")
        voto_service.blockchain.mine_pending_transactions()

        totalizacao = totalizacao_service.totalizar_votos()

        # Deve contar apenas os 2 votos válidos
        assert len(totalizacao.votos_totalizados) == 1

    def test_totalizacao_data_hora(self, totalizacao_service, voto_service, candidato_prefeito):
        """Testa que a totalização tem data e hora"""
        voto_service.votar(candidato_prefeito)
        totalizacao = totalizacao_service.totalizar_votos()

        assert totalizacao.data_hora is not None

    def test_totalizacao_id_incrementado(self, totalizacao_service, voto_service, candidato_prefeito):
        """Testa que o ID da totalização é sempre 1 (pode ser modificado no futuro)"""
        voto_service.votar(candidato_prefeito)
        totalizacao = totalizacao_service.totalizar_votos()

        assert totalizacao.id == 1

    @pytest.mark.parametrize("num_votos_candidato1,num_votos_candidato2", [
        (1, 0),
        (5, 3),
        (10, 10),
        (0, 5),
        (50, 25),
    ])
    def test_totalizar_diferentes_distribuicoes_votos(
        self, totalizacao_service, voto_service, candidato_prefeito,
        candidato_vereador, num_votos_candidato1, num_votos_candidato2
    ):
        """Testa totalização com diferentes distribuições de votos"""
        for i in range(num_votos_candidato1):
            voto_service.votar(candidato_prefeito)

        for i in range(num_votos_candidato2):
            voto_service.votar(candidato_vereador)

        totalizacao = totalizacao_service.totalizar_votos()

        candidatos_com_votos = len([v for v in [num_votos_candidato1, num_votos_candidato2] if v > 0])
        assert len(totalizacao.votos_totalizados) == candidatos_com_votos

    def test_assinatura_totalizacao_valida(
        self, totalizacao_service, voto_service, candidato_prefeito
    ):
        """Testa que a assinatura da totalização pode ser verificada"""
        voto_service.votar(candidato_prefeito)
        totalizacao = totalizacao_service.totalizar_votos()

        # Verifica a assinatura
        totalizacao_dict = totalizacao.dict(exclude_none=True, exclude={'assinatura'})
        assinatura = base64.b64decode(totalizacao.assinatura)

        resultado = totalizacao_service.criptografia_service.verificar_assinatura(
            json.dumps(totalizacao_dict, default=datetime_to_string, sort_keys=True),
            assinatura
        )
        assert resultado is True
