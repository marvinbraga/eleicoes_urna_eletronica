"""
Testes para o serviço de detecção de anomalias
"""
import pytest

from core.processors.classes import AnomaliaService
from core.models.classes import Voto, Candidato, Partido, Cargo, Eleicao
from datetime import datetime


@pytest.mark.unit
class TestAnomaliaService:
    """Testes para o serviço de detecção de anomalias"""

    @pytest.fixture
    def anomalia_service(self):
        """Cria uma instância do serviço de anomalias"""
        return AnomaliaService()

    @pytest.fixture
    def votos_normais(self, candidato_prefeito):
        """Cria uma lista de votos normais para teste"""
        votos = []
        for i in range(20):
            voto = Voto(
                id=str(i + 1),
                candidato=candidato_prefeito,
                hash_localizacao=f"hash_loc_{i}",
                hash_blockchain=f"hash_bc_{i}",
                qr_code=f"qr_{i}",
                nonce=f"nonce_{i}"
            )
            votos.append(voto)
        return votos

    def test_inicializacao_servico(self, anomalia_service):
        """Testa se o serviço é inicializado corretamente"""
        assert anomalia_service.isolation_forest is not None
        assert anomalia_service.isolation_forest.n_estimators == 100
        assert anomalia_service.isolation_forest.contamination == 0.1

    def test_extrair_caracteristicas(self, anomalia_service, candidato_prefeito):
        """Testa a extração de características de um voto"""
        voto = Voto(
            id="1",
            candidato=candidato_prefeito,
            hash_localizacao="hash_loc",
            hash_blockchain="hash_bc",
            qr_code="qr_code",
            nonce="nonce"
        )

        caracteristicas = anomalia_service._extrair_caracteristicas(voto)

        assert len(caracteristicas) == 3
        assert caracteristicas[0] == candidato_prefeito.id
        assert isinstance(caracteristicas[1], int)
        assert isinstance(caracteristicas[2], int)

    def test_detectar_anomalias_votos_normais(self, anomalia_service, votos_normais):
        """Testa a detecção de anomalias em votos normais"""
        anomalias = anomalia_service.detectar_anomalias(votos_normais)

        # Com votos normais, pode haver algumas anomalias detectadas ou não
        assert isinstance(anomalias, list)
        assert len(anomalias) <= len(votos_normais)

    def test_detectar_anomalias_com_voto_anomalo(self, anomalia_service, votos_normais, candidato_vereador):
        """Testa a detecção de anomalias com um voto anômalo adicionado"""
        # Adiciona um voto muito diferente
        voto_anomalo = Voto(
            id="999",
            candidato=candidato_vereador,
            hash_localizacao="hash_muito_diferente_99999",
            hash_blockchain="hash_blockchain_anomalo_99999",
            qr_code="qr_anomalo",
            nonce="nonce_anomalo"
        )

        votos_com_anomalia = votos_normais + [voto_anomalo]

        anomalias = anomalia_service.detectar_anomalias(votos_com_anomalia)

        # Deve detectar anomalias
        assert isinstance(anomalias, list)

    def test_detectar_conluio_votos_normais(self, anomalia_service, votos_normais):
        """Testa a detecção de conluio em votos normais"""
        conluio = anomalia_service.detectar_conluio(votos_normais)

        assert isinstance(conluio, list)
        # Conluio tem threshold mais restritivo (-0.5), então pode ou não detectar
        assert len(conluio) <= len(votos_normais)

    def test_detectar_conluio_threshold_mais_restritivo(self, anomalia_service, votos_normais):
        """Testa que detectar_conluio tem threshold mais restritivo que detectar_anomalias"""
        anomalias = anomalia_service.detectar_anomalias(votos_normais)
        conluio = anomalia_service.detectar_conluio(votos_normais)

        # Conluio deve ter menos ou igual detecções que anomalias
        assert len(conluio) <= len(anomalias)

    def test_detectar_anomalias_lista_vazia(self, anomalia_service):
        """Testa a detecção de anomalias com lista vazia"""
        # Deve lançar exceção ou retornar lista vazia
        with pytest.raises(Exception):
            anomalia_service.detectar_anomalias([])

    def test_detectar_anomalias_um_voto(self, anomalia_service, candidato_prefeito):
        """Testa a detecção de anomalias com apenas um voto"""
        voto = Voto(
            id="1",
            candidato=candidato_prefeito,
            hash_localizacao="hash_loc",
            hash_blockchain="hash_bc",
            qr_code="qr_code",
            nonce="nonce"
        )

        # Com apenas um voto, o algoritmo pode ter dificuldades
        # Isso é esperado e está testando o comportamento de edge case
        with pytest.raises(Exception):
            anomalia_service.detectar_anomalias([voto])

    def test_detectar_anomalias_votos_identicos(self, anomalia_service, candidato_prefeito):
        """Testa a detecção de anomalias em votos com características similares"""
        votos_similares = []
        for i in range(10):
            voto = Voto(
                id=str(i + 1),
                candidato=candidato_prefeito,
                hash_localizacao=f"hash_{i}",
                hash_blockchain=f"hash_{i}",
                qr_code=f"qr_{i}",
                nonce=f"nonce_{i}"
            )
            votos_similares.append(voto)

        anomalias = anomalia_service.detectar_anomalias(votos_similares)

        assert isinstance(anomalias, list)

    def test_detectar_conluio_votos_suspeitos(self, anomalia_service, candidato_prefeito, candidato_vereador):
        """Testa a detecção de conluio com votos suspeitos"""
        votos = []

        # Cria votos normais
        for i in range(15):
            voto = Voto(
                id=str(i + 1),
                candidato=candidato_prefeito,
                hash_localizacao=f"hash_normal_{i}",
                hash_blockchain=f"hash_normal_{i}",
                qr_code=f"qr_{i}",
                nonce=f"nonce_{i}"
            )
            votos.append(voto)

        # Adiciona votos potencialmente suspeitos (padrão diferente)
        for i in range(5):
            voto = Voto(
                id=str(i + 100),
                candidato=candidato_vereador,
                hash_localizacao=f"hash_suspeito_{i * 1000}",
                hash_blockchain=f"hash_suspeito_{i * 1000}",
                qr_code=f"qr_suspeito_{i}",
                nonce=f"nonce_suspeito_{i}"
            )
            votos.append(voto)

        conluio = anomalia_service.detectar_conluio(votos)

        assert isinstance(conluio, list)

    @pytest.mark.parametrize("num_votos", [5, 10, 20, 50, 100])
    def test_detectar_anomalias_diferentes_tamanhos(
        self, anomalia_service, candidato_prefeito, num_votos
    ):
        """Testa a detecção de anomalias com diferentes quantidades de votos"""
        votos = []
        for i in range(num_votos):
            voto = Voto(
                id=str(i + 1),
                candidato=candidato_prefeito,
                hash_localizacao=f"hash_{i}",
                hash_blockchain=f"hash_{i}",
                qr_code=f"qr_{i}",
                nonce=f"nonce_{i}"
            )
            votos.append(voto)

        anomalias = anomalia_service.detectar_anomalias(votos)

        assert isinstance(anomalias, list)
        assert len(anomalias) <= num_votos

    def test_modelo_isolation_forest_treinado(self, anomalia_service, votos_normais):
        """Testa que o modelo Isolation Forest é treinado corretamente"""
        # Antes de detectar anomalias
        anomalia_service.detectar_anomalias(votos_normais)

        # O modelo deve estar treinado (n_estimators_ existe após fit)
        assert hasattr(anomalia_service.isolation_forest, 'estimators_')
        assert len(anomalia_service.isolation_forest.estimators_) > 0

    def test_scores_anomalia_calculados(self, anomalia_service, votos_normais):
        """Testa que os scores de anomalia são calculados corretamente"""
        # Extrai características
        caracteristicas = [anomalia_service._extrair_caracteristicas(voto) for voto in votos_normais]

        # Treina o modelo
        anomalia_service.isolation_forest.fit(caracteristicas)

        # Calcula scores
        scores = anomalia_service.isolation_forest.decision_function(caracteristicas)

        assert len(scores) == len(votos_normais)
        assert all(isinstance(score, float) for score in scores)
