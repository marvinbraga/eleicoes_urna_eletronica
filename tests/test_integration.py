"""
Testes de integração para o sistema de votação eletrônica
"""
import pytest

from core.processors.classes import SistemaVotacao
from core.models.classes import Candidato, Partido, Cargo, Eleicao
from datetime import datetime


@pytest.mark.integration
class TestIntegracaoSistemaVotacao:
    """Testes de integração do sistema completo de votação"""

    def test_fluxo_completo_votacao(
        self, sistema_votacao, candidato_prefeito, candidato_vereador
    ):
        """
        Testa o fluxo completo de votação:
        1. Registrar votos
        2. Gerar registro impresso
        3. Validar votos
        4. Gerar boletim de urna
        5. Validar boletim
        6. Totalizar votos
        7. Verificar integridade da totalização
        8. Detectar anomalias
        9. Detectar conluio
        """
        # 1. Registrar votos
        voto1 = sistema_votacao.votar(candidato_prefeito)
        voto2 = sistema_votacao.votar(candidato_vereador)
        voto3 = sistema_votacao.votar(candidato_prefeito)

        assert voto1 is not None
        assert voto2 is not None
        assert voto3 is not None

        # 2. Gerar registros impressos
        registro1 = sistema_votacao.gerar_registro_impresso(voto1)
        registro2 = sistema_votacao.gerar_registro_impresso(voto2)
        registro3 = sistema_votacao.gerar_registro_impresso(voto3)

        assert registro1 is not None
        assert registro2 is not None
        assert registro3 is not None

        # 3. Validar votos
        registros_impressos = [registro1, registro2, registro3]
        votos_validos = sistema_votacao.validar_votos(registros_impressos)

        assert votos_validos is True

        # 4. Gerar boletim de urna
        boletim_urna = sistema_votacao.gerar_boletim_urna()

        assert boletim_urna is not None
        assert len(boletim_urna.votos) == 3

        # 5. Validar boletim
        boletim_valido = sistema_votacao.validar_boletim_urna(boletim_urna)

        assert boletim_valido is True

        # 6. Totalizar votos
        totalizacao = sistema_votacao.totalizar_votos()

        assert totalizacao is not None
        assert len(totalizacao.votos_totalizados) == 2  # 2 candidatos diferentes

        # 7. Verificar integridade da totalização
        totalizacao_integra = sistema_votacao.verificar_integridade_totalizacao(totalizacao)

        assert totalizacao_integra is True

        # 8. Detectar anomalias
        votos_totalizados = totalizacao.votos_totalizados
        anomalias = sistema_votacao.detectar_anomalias(votos_totalizados)

        assert isinstance(anomalias, list)

        # 9. Detectar conluio
        conluio_suspeito = sistema_votacao.detectar_conluio(votos_totalizados)

        assert isinstance(conluio_suspeito, list)

    def test_multiplos_cargos_e_candidatos(self, sistema_votacao, eleicao_exemplo):
        """Testa votação com múltiplos cargos e candidatos"""
        # Cria mais candidatos
        partido1 = Partido(numero=10, sigla="P1", nome="Partido 1")
        partido2 = Partido(numero=20, sigla="P2", nome="Partido 2")

        cargo_prefeito = Cargo(id=1, nome="Prefeito", eleicao=eleicao_exemplo.id)
        cargo_vereador = Cargo(id=2, nome="Vereador", eleicao=eleicao_exemplo.id)

        candidatos = [
            Candidato(
                id=1, nome="Candidato Prefeito 1", partido=partido1,
                codigo="10100", foto="foto1.jpg", cargo=cargo_prefeito,
                eleicao=eleicao_exemplo
            ),
            Candidato(
                id=2, nome="Candidato Prefeito 2", partido=partido2,
                codigo="20200", foto="foto2.jpg", cargo=cargo_prefeito,
                eleicao=eleicao_exemplo
            ),
            Candidato(
                id=3, nome="Candidato Vereador 1", partido=partido1,
                codigo="10001", foto="foto3.jpg", cargo=cargo_vereador,
                eleicao=eleicao_exemplo
            ),
            Candidato(
                id=4, nome="Candidato Vereador 2", partido=partido2,
                codigo="20002", foto="foto4.jpg", cargo=cargo_vereador,
                eleicao=eleicao_exemplo
            ),
        ]

        # Vota em todos os candidatos
        votos = []
        for candidato in candidatos:
            voto = sistema_votacao.votar(candidato)
            votos.append(voto)

        # Totaliza
        totalizacao = sistema_votacao.totalizar_votos()

        assert len(totalizacao.votos_totalizados) == 4

    def test_cenario_erro_voto_invalido(self, sistema_votacao, candidato_prefeito):
        """Testa cenário onde um voto é modificado (fraude)"""
        # Registra votos válidos
        voto1 = sistema_votacao.votar(candidato_prefeito)
        voto2 = sistema_votacao.votar(candidato_prefeito)

        # Gera registros impressos
        registro1 = sistema_votacao.gerar_registro_impresso(voto1)

        # Cria um registro impresso modificado
        from core.models.classes import Voto, RegistroImpresso

        voto_modificado = Voto(
            id=str(voto2.id),
            candidato=candidato_prefeito,
            hash_localizacao="hash_modificado",  # Hash modificado
            hash_blockchain=voto2.hash_blockchain,
            qr_code=voto2.qr_code,
            nonce=voto2.nonce
        )

        registro2_modificado = RegistroImpresso(
            voto=voto_modificado,
            data_hora=voto2.data_hora
        )

        # Tenta validar
        registros = [registro1, registro2_modificado]
        votos_validos = sistema_votacao.validar_votos(registros)

        # Deve falhar na validação
        assert votos_validos is False

    def test_cenario_blockchain_integridade(self, sistema_votacao, candidato_prefeito):
        """Testa a integridade da blockchain após múltiplas votações"""
        # Registra múltiplos votos
        for i in range(10):
            sistema_votacao.votar(candidato_prefeito)

        # Verifica integridade da blockchain
        blockchain_valida = sistema_votacao.blockchain.is_chain_valid()

        assert blockchain_valida is True

    def test_cenario_boletim_urna_modificado(self, sistema_votacao, candidato_prefeito):
        """Testa detecção de boletim de urna modificado"""
        sistema_votacao.votar(candidato_prefeito)

        # Gera boletim
        boletim = sistema_votacao.gerar_boletim_urna()

        # Modifica o boletim
        boletim.secao = "Seção Modificada"

        # Tenta validar
        boletim_valido = sistema_votacao.validar_boletim_urna(boletim)

        # Deve falhar
        assert boletim_valido is False

    def test_cenario_grande_volume_votos(self, sistema_votacao, candidato_prefeito, candidato_vereador):
        """Testa o sistema com grande volume de votos"""
        # Registra 100 votos
        for i in range(50):
            sistema_votacao.votar(candidato_prefeito)

        for i in range(50):
            sistema_votacao.votar(candidato_vereador)

        # Totaliza
        totalizacao = sistema_votacao.totalizar_votos()

        assert len(totalizacao.votos_totalizados) == 2

        # Gera boletim
        boletim = sistema_votacao.gerar_boletim_urna()

        assert len(boletim.votos) == 100

        # Verifica integridade
        assert sistema_votacao.validar_boletim_urna(boletim) is True
        assert sistema_votacao.verificar_integridade_totalizacao(totalizacao) is True

    def test_cenario_sem_votos(self, sistema_votacao):
        """Testa o sistema quando não há votos registrados"""
        # Gera boletim sem votos
        boletim = sistema_votacao.gerar_boletim_urna()

        assert len(boletim.votos) == 0
        assert sistema_votacao.validar_boletim_urna(boletim) is True

        # Totaliza sem votos
        totalizacao = sistema_votacao.totalizar_votos()

        assert len(totalizacao.votos_totalizados) == 0
        assert sistema_votacao.verificar_integridade_totalizacao(totalizacao) is True

    def test_registro_urna_gerado(self, sistema_votacao, candidato_prefeito):
        """Testa a geração de registro de urna"""
        sistema_votacao.votar(candidato_prefeito)

        boletim = sistema_votacao.gerar_boletim_urna()
        registro_urna = sistema_votacao.gerar_registro_urna(boletim)

        assert registro_urna is not None
        assert registro_urna.boletim_urna_eletronico == boletim
        assert registro_urna.boletim_urna_escaneado is not None

    @pytest.mark.parametrize("num_votos_prefeito,num_votos_vereador", [
        (5, 0),
        (0, 5),
        (10, 10),
        (25, 15),
        (50, 50),
    ])
    def test_diferentes_distribuicoes_votos(
        self, sistema_votacao, candidato_prefeito, candidato_vereador,
        num_votos_prefeito, num_votos_vereador
    ):
        """Testa o sistema com diferentes distribuições de votos"""
        for i in range(num_votos_prefeito):
            sistema_votacao.votar(candidato_prefeito)

        for i in range(num_votos_vereador):
            sistema_votacao.votar(candidato_vereador)

        totalizacao = sistema_votacao.totalizar_votos()

        candidatos_esperados = 0
        if num_votos_prefeito > 0:
            candidatos_esperados += 1
        if num_votos_vereador > 0:
            candidatos_esperados += 1

        assert len(totalizacao.votos_totalizados) == candidatos_esperados

    def test_deteccao_anomalias_apos_votacao(self, sistema_votacao, candidato_prefeito):
        """Testa detecção de anomalias após votação normal"""
        # Registra votos
        for i in range(20):
            sistema_votacao.votar(candidato_prefeito)

        # Totaliza
        totalizacao = sistema_votacao.totalizar_votos()

        # Detecta anomalias
        anomalias = sistema_votacao.detectar_anomalias(totalizacao.votos_totalizados)

        # Não deve haver muitas anomalias em votos normais
        assert isinstance(anomalias, list)
        assert len(anomalias) <= len(totalizacao.votos_totalizados)
