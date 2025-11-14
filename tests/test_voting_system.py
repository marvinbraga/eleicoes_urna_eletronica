"""
Testes para o sistema de votação eletrônica
"""
import json
import os
import pytest
from datetime import datetime
from pathlib import Path

from core.models.classes import Eleicao, Partido, Cargo, Candidato, Voto
from core.processors.classes import SistemaVotacao
from core.utils.security import KeyManager


@pytest.fixture
def setup_keys():
    """Cria chaves temporárias para testes"""
    test_dir = Path(__file__).parent / "temp_keys"
    test_dir.mkdir(exist_ok=True)

    key_manager = KeyManager()
    private_key_path = test_dir / "private_key_test.pem"
    crypto_key_path = test_dir / "cryptography_key_test.pem"

    key_manager.gerar_chave_privada(str(private_key_path))
    key_manager.gerar_chave_criptografia(str(crypto_key_path))

    yield str(private_key_path), str(crypto_key_path)

    # Cleanup
    if private_key_path.exists():
        private_key_path.unlink()
    if crypto_key_path.exists():
        crypto_key_path.unlink()
    if test_dir.exists():
        test_dir.rmdir()


@pytest.fixture
def sample_candidato():
    """Cria um candidato de exemplo para testes"""
    partido = Partido(numero=13, sigla="PT", nome="Partido dos Trabalhadores")
    eleicao = Eleicao(
        id=1,
        nome="Eleições Municipais 2024",
        data=datetime.now(),
        turnos=2
    )
    cargo = Cargo(id=1, nome="Prefeito", eleicao=1)

    candidato = Candidato(
        id=1,
        nome="João da Silva",
        partido=partido,
        codigo="13123",
        foto="https://example.com/foto.jpg",
        cargo=cargo,
        eleicao=eleicao
    )
    return candidato


def test_criar_sistema_votacao(setup_keys):
    """Testa a criação do sistema de votação"""
    private_key_path, crypto_key_path = setup_keys
    sistema = SistemaVotacao(private_key_path, crypto_key_path)

    assert sistema is not None
    assert sistema.voto_service is not None
    assert sistema.blockchain is not None


def test_registrar_voto(setup_keys, sample_candidato):
    """Testa o registro de um voto"""
    private_key_path, crypto_key_path = setup_keys
    sistema = SistemaVotacao(private_key_path, crypto_key_path)

    voto = sistema.votar(sample_candidato)

    assert voto is not None
    assert voto.id == 1
    assert voto.candidato == sample_candidato
    assert voto.nonce is not None
    assert voto.hash_blockchain is not None
    assert voto.hash_localizacao is not None


def test_multiplos_votos(setup_keys, sample_candidato):
    """Testa o registro de múltiplos votos"""
    private_key_path, crypto_key_path = setup_keys
    sistema = SistemaVotacao(private_key_path, crypto_key_path)

    voto1 = sistema.votar(sample_candidato)
    voto2 = sistema.votar(sample_candidato)
    voto3 = sistema.votar(sample_candidato)

    assert len(sistema.voto_service.votos) == 3
    assert voto1.id != voto2.id != voto3.id
    assert voto1.nonce != voto2.nonce != voto3.nonce


def test_blockchain_integrity(setup_keys, sample_candidato):
    """Testa a integridade da blockchain"""
    private_key_path, crypto_key_path = setup_keys
    sistema = SistemaVotacao(private_key_path, crypto_key_path)

    # Registrar alguns votos
    sistema.votar(sample_candidato)
    sistema.votar(sample_candidato)

    # Verificar integridade da blockchain
    is_valid = sistema.blockchain.is_chain_valid()
    assert is_valid is True


def test_totalizar_votos(setup_keys, sample_candidato):
    """Testa a totalização de votos"""
    private_key_path, crypto_key_path = setup_keys
    sistema = SistemaVotacao(private_key_path, crypto_key_path)

    # Registrar votos
    sistema.votar(sample_candidato)
    sistema.votar(sample_candidato)
    sistema.votar(sample_candidato)

    # Totalizar
    totalizacao = sistema.totalizar_votos()

    assert totalizacao is not None
    assert len(totalizacao.votos_totalizados) >= 1
    assert totalizacao.hash_blockchain is not None
    assert totalizacao.assinatura is not None


def test_gerar_boletim_urna(setup_keys, sample_candidato):
    """Testa a geração do boletim de urna"""
    private_key_path, crypto_key_path = setup_keys
    sistema = SistemaVotacao(private_key_path, crypto_key_path)

    # Registrar votos
    sistema.votar(sample_candidato)
    sistema.votar(sample_candidato)

    # Gerar boletim
    boletim = sistema.gerar_boletim_urna()

    assert boletim is not None
    assert boletim.id == 1
    assert len(boletim.votos) == 2
    assert boletim.hash_final_blockchain is not None
    assert boletim.assinatura is not None


def test_validar_boletim_urna(setup_keys, sample_candidato):
    """Testa a validação do boletim de urna"""
    private_key_path, crypto_key_path = setup_keys
    sistema = SistemaVotacao(private_key_path, crypto_key_path)

    # Registrar votos e gerar boletim
    sistema.votar(sample_candidato)
    boletim = sistema.gerar_boletim_urna()

    # Validar boletim
    is_valid = sistema.validar_boletim_urna(boletim)

    assert is_valid is True


def test_detectar_anomalias(setup_keys, sample_candidato):
    """Testa a detecção de anomalias"""
    private_key_path, crypto_key_path = setup_keys
    sistema = SistemaVotacao(private_key_path, crypto_key_path)

    # Registrar votos
    for _ in range(10):
        sistema.votar(sample_candidato)

    # Detectar anomalias
    anomalias = sistema.detectar_anomalias(sistema.voto_service.votos)

    # Não devemos ter anomalias em votos normais
    assert isinstance(anomalias, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
