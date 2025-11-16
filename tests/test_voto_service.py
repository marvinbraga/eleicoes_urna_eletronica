"""
Testes para o serviço de votação
"""
import base64
import json
import pytest

from core.processors.classes import (
    VotoService, CriptografiaService, IntegrityVerifier,
    NonceGenerator, AuditLogger
)
from core.blockchain.classes import Blockchain
from core.models.classes import RegistroImpresso, Voto


@pytest.mark.unit
class TestVotoService:
    """Testes para o serviço de votação"""

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

    def test_inicializacao_servico(self, voto_service):
        """Testa se o serviço é inicializado corretamente"""
        assert voto_service.criptografia_service is not None
        assert voto_service.blockchain is not None
        assert voto_service.integrity_verifier is not None
        assert voto_service.nonce_generator is not None
        assert voto_service.audit_logger is not None
        assert len(voto_service.votos) == 0

    def test_votar_candidato(self, voto_service, candidato_prefeito):
        """Testa o registro de um voto"""
        voto = voto_service.votar(candidato_prefeito)

        assert voto is not None
        assert voto.candidato == candidato_prefeito
        assert voto.id == 1
        assert voto.nonce is not None
        assert len(voto_service.votos) == 1

    def test_votar_multiplos_candidatos(self, voto_service, candidato_prefeito, candidato_vereador):
        """Testa o registro de múltiplos votos"""
        voto1 = voto_service.votar(candidato_prefeito)
        voto2 = voto_service.votar(candidato_vereador)

        assert len(voto_service.votos) == 2
        assert voto1.id == 1
        assert voto2.id == 2
        assert voto1.nonce != voto2.nonce

    def test_voto_adicionado_blockchain(self, voto_service, candidato_prefeito):
        """Testa se o voto é adicionado à blockchain"""
        tamanho_inicial = len(voto_service.blockchain.chain)
        voto_service.votar(candidato_prefeito)

        # Deve ter adicionado um novo bloco
        assert len(voto_service.blockchain.chain) > tamanho_inicial

    def test_voto_criptografado(self, voto_service, candidato_prefeito):
        """Testa se o voto é criptografado antes de ser adicionado à blockchain"""
        voto_service.votar(candidato_prefeito)

        # Pega a última transação
        ultimo_bloco = voto_service.blockchain.chain[-1]
        transacao = ultimo_bloco.transactions[0]

        # A transação deve ser uma string (voto criptografado)
        assert isinstance(transacao, str)

        # Tenta descriptografar para verificar
        voto_descriptografado = voto_service.criptografia_service.descriptografar_dados(transacao)
        voto_assinado = json.loads(voto_descriptografado)

        assert "voto" in voto_assinado
        assert "assinatura" in voto_assinado

    def test_voto_assinado(self, voto_service, candidato_prefeito):
        """Testa se o voto é assinado corretamente"""
        voto_service.votar(candidato_prefeito)

        # Pega a última transação e descriptografa
        ultimo_bloco = voto_service.blockchain.chain[-1]
        transacao = ultimo_bloco.transactions[0]
        voto_descriptografado = voto_service.criptografia_service.descriptografar_dados(transacao)
        voto_assinado = json.loads(voto_descriptografado)

        # Verifica a assinatura
        voto_json = voto_assinado["voto"]
        assinatura = base64.b64decode(voto_assinado["assinatura"])

        assert voto_service.criptografia_service.verificar_assinatura(voto_json, assinatura) is True

    def test_nonce_unico_por_voto(self, voto_service, candidato_prefeito):
        """Testa que cada voto tem um nonce único"""
        voto1 = voto_service.votar(candidato_prefeito)
        voto2 = voto_service.votar(candidato_prefeito)
        voto3 = voto_service.votar(candidato_prefeito)

        nonces = {voto1.nonce, voto2.nonce, voto3.nonce}
        assert len(nonces) == 3  # Todos diferentes

    def test_validar_votos_sucesso(self, voto_service, candidato_prefeito):
        """Testa a validação de votos válidos"""
        voto = voto_service.votar(candidato_prefeito)
        registro_impresso = RegistroImpresso(voto=voto, data_hora=voto.data_hora)

        resultado = voto_service.validar_votos([registro_impresso])
        assert resultado is True

    def test_validar_votos_multiplos(self, voto_service, candidato_prefeito, candidato_vereador):
        """Testa a validação de múltiplos votos"""
        voto1 = voto_service.votar(candidato_prefeito)
        voto2 = voto_service.votar(candidato_vereador)

        registro1 = RegistroImpresso(voto=voto1, data_hora=voto1.data_hora)
        registro2 = RegistroImpresso(voto=voto2, data_hora=voto2.data_hora)

        resultado = voto_service.validar_votos([registro1, registro2])
        assert resultado is True

    def test_validar_votos_voto_inexistente(self, voto_service, candidato_prefeito):
        """Testa a validação com voto inexistente"""
        voto_falso = Voto(
            id="999",
            candidato=candidato_prefeito,
            hash_localizacao="hash_falso",
            hash_blockchain="hash_falso",
            qr_code="qr_falso",
            nonce="nonce_falso"
        )

        registro_falso = RegistroImpresso(voto=voto_falso, data_hora=voto_falso.data_hora)

        resultado = voto_service.validar_votos([registro_falso])
        assert resultado is False

    def test_processar_votos_validos(self, voto_service, candidato_prefeito):
        """Testa o processamento de votos válidos"""
        # Registra um voto
        voto_service.votar(candidato_prefeito)

        # Pega o voto criptografado da blockchain
        ultimo_bloco = voto_service.blockchain.chain[-1]
        voto_criptografado = ultimo_bloco.transactions[0]

        # Limpa os votos para simular processamento
        voto_service.votos.clear()

        # Processa o voto
        voto_service.processar_votos([voto_criptografado])

        # O voto deve ter sido adicionado
        assert len(voto_service.votos) == 1

    def test_processar_votos_duplicados_nao_aceitos(self, voto_service, candidato_prefeito):
        """Testa que votos duplicados (mesmo nonce) não são aceitos"""
        # Registra um voto
        voto_service.votar(candidato_prefeito)

        # Pega o voto criptografado
        ultimo_bloco = voto_service.blockchain.chain[-1]
        voto_criptografado = ultimo_bloco.transactions[0]

        # Tenta processar o mesmo voto novamente
        voto_service.processar_votos([voto_criptografado])

        # Não deve adicionar voto duplicado
        assert len(voto_service.votos) == 1

    def test_processar_voto_com_assinatura_invalida(self, voto_service, candidato_prefeito, chaves_criptografia):
        """Testa que votos com assinatura inválida são rejeitados"""
        # Cria um voto falso com assinatura inválida
        voto = Voto(
            id="1",
            candidato=candidato_prefeito,
            hash_localizacao="hash",
            hash_blockchain="hash",
            qr_code="qr",
            nonce="nonce123"
        )

        voto_assinado = {
            "voto": voto.json(),
            "assinatura": base64.b64encode(b"assinatura_invalida").decode()
        }

        voto_criptografado = voto_service.criptografia_service.criptografar_dados(json.dumps(voto_assinado))

        # Processa o voto inválido
        voto_service.processar_votos([voto_criptografado])

        # Não deve adicionar o voto
        assert len(voto_service.votos) == 0

    def test_hash_blockchain_atualizado(self, voto_service, candidato_prefeito):
        """Testa que o hash da blockchain é atualizado a cada voto"""
        hash_inicial = voto_service.blockchain.chain[-1].hash

        voto_service.votar(candidato_prefeito)

        hash_final = voto_service.blockchain.chain[-1].hash

        assert hash_inicial != hash_final

    def test_voto_registrado_em_auditoria(self, voto_service, candidato_prefeito, tmp_path, monkeypatch):
        """Testa que o voto é registrado no log de auditoria"""
        # Este teste verifica se o audit_logger.log é chamado
        # Em produção, verificaríamos o arquivo de log

        log_chamado = []

        def mock_log(message):
            log_chamado.append(message)

        monkeypatch.setattr(voto_service.audit_logger, "log", mock_log)

        voto_service.votar(candidato_prefeito)

        assert len(log_chamado) > 0
        assert "Voto registrado" in log_chamado[0]

    @pytest.mark.parametrize("numero_votos", [1, 5, 10, 20])
    def test_votar_multiplos_votos_sequencial(self, voto_service, candidato_prefeito, numero_votos):
        """Testa o registro de vários votos sequencialmente"""
        for i in range(numero_votos):
            voto = voto_service.votar(candidato_prefeito)
            assert voto.id == i + 1

        assert len(voto_service.votos) == numero_votos
