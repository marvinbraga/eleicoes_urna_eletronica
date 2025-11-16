"""
Testes de performance para as otimizações implementadas.
"""
import time
import pytest
from unittest.mock import Mock

from core.blockchain.classes import Blockchain
from core.repositories.base import BaseRepository
from core.utils.cache import CacheManager, cached


class TestBlockchainPerformance:
    """Testes de performance da blockchain otimizada."""

    def test_hash_index_performance(self):
        """Testa performance da busca por hash usando índice."""
        blockchain = Blockchain()

        # Adicionar 1000 blocos
        for i in range(1000):
            blockchain.add_transaction(f"transaction_{i}")
            blockchain.mine_pending_transactions()

        # Buscar bloco no meio da cadeia
        target_block = blockchain.chain[500]

        # Medir tempo de busca
        start = time.time()
        found_block = blockchain.get_block_by_hash(target_block.hash)
        elapsed = time.time() - start

        assert found_block is not None
        assert found_block.hash == target_block.hash
        # Busca deve ser muito rápida (< 1ms)
        assert elapsed < 0.001, f"Busca levou {elapsed*1000:.2f}ms, esperado < 1ms"

    def test_block_cache_performance(self):
        """Testa performance do cache de blocos."""
        blockchain = Blockchain()

        # Adicionar blocos
        for i in range(100):
            blockchain.add_transaction(f"transaction_{i}")
            blockchain.mine_pending_transactions()

        # Primeira busca (sem cache)
        start = time.time()
        block1 = blockchain.get_block_by_index(50)
        first_elapsed = time.time() - start

        # Segunda busca (com cache)
        start = time.time()
        block2 = blockchain.get_block_by_index(50)
        second_elapsed = time.time() - start

        assert block1 is block2  # Mesmo objeto (cache)
        # Cache deve ser mais rápido
        assert second_elapsed <= first_elapsed

    def test_chain_stats(self):
        """Testa estatísticas da blockchain."""
        blockchain = Blockchain()

        for i in range(10):
            blockchain.add_transaction(f"transaction_{i}")
            blockchain.mine_pending_transactions()

        stats = blockchain.get_chain_stats()

        assert stats['total_blocks'] == 11  # 10 + genesis
        assert stats['pending_transactions'] == 0
        assert stats['cache_size'] > 0
        assert stats['index_size'] == 11


class TestRepositoryPerformance:
    """Testes de performance dos repositórios."""

    def setup_method(self):
        """Setup para cada teste."""
        from fakeredis import FakeRedis
        self.redis_client = FakeRedis(decode_responses=True)
        self.repo = BaseRepository(self.redis_client, "test")

    def test_compression_large_data(self):
        """Testa compressão de dados grandes."""
        # Dados pequenos (não devem ser comprimidos)
        small_data = "x" * 500
        compressed_small = self.repo._compress_data(small_data)
        assert not compressed_small.startswith(b'GZIP:')

        # Dados grandes (devem ser comprimidos)
        large_data = "x" * 2000
        compressed_large = self.repo._compress_data(large_data)
        assert compressed_large.startswith(b'GZIP:')
        assert len(compressed_large) < len(large_data.encode())

    def test_pagination_performance(self):
        """Testa performance da paginação."""
        # Adicionar 100 itens
        for i in range(100):
            self.repo.save(i, {"id": i, "data": f"test_{i}"})

        # Testar paginação
        start = time.time()
        result = self.repo.get_paginated(skip=20, limit=10)
        elapsed = time.time() - start

        assert len(result['items']) == 10
        assert result['total'] == 100
        assert result['page'] == 3
        assert result['pages'] == 10
        # Deve ser rápido
        assert elapsed < 0.1, f"Paginação levou {elapsed*1000:.2f}ms"

    def test_bulk_operations(self):
        """Testa operações em massa."""
        # Salvar 1000 itens
        start = time.time()
        for i in range(1000):
            self.repo.save(i, {"id": i, "data": f"test_{i}"})
        save_elapsed = time.time() - start

        # Buscar todos
        start = time.time()
        items = self.repo.get_all(limit=1000)
        get_elapsed = time.time() - start

        assert len(items) == 1000
        # Verificar performance aceitável
        assert save_elapsed < 2.0, f"Save de 1000 itens levou {save_elapsed:.2f}s"
        assert get_elapsed < 0.5, f"Get de 1000 itens levou {get_elapsed:.2f}s"


class TestCachePerformance:
    """Testes de performance do cache."""

    def setup_method(self):
        """Setup para cada teste."""
        self.cache = CacheManager(maxsize=100, ttl=60)

    def test_cache_hit_performance(self):
        """Testa performance de cache hit."""
        # Adicionar ao cache
        self.cache.set("test_key", {"data": "test"})

        # Medir tempo de hit
        times = []
        for _ in range(1000):
            start = time.time()
            value = self.cache.get("test_key")
            elapsed = time.time() - start
            times.append(elapsed)
            assert value is not None

        avg_time = sum(times) / len(times)
        # Cache hit deve ser muito rápido (< 0.01ms)
        assert avg_time < 0.00001, f"Cache hit médio: {avg_time*1000000:.2f}µs"

    def test_cache_decorator_performance(self):
        """Testa performance do decorator de cache."""
        call_count = 0

        @cached(key_prefix="test")
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            time.sleep(0.01)  # Simular operação cara
            return x * 2

        # Primeira chamada (sem cache)
        start = time.time()
        result1 = expensive_function(5)
        first_elapsed = time.time() - start

        # Segunda chamada (com cache)
        start = time.time()
        result2 = expensive_function(5)
        second_elapsed = time.time() - start

        assert result1 == result2 == 10
        assert call_count == 1  # Função chamada apenas uma vez
        # Cache deve ser muito mais rápido
        assert second_elapsed < first_elapsed / 10

    def test_cache_stats_accuracy(self):
        """Testa precisão das estatísticas do cache."""
        # Adicionar alguns valores
        for i in range(10):
            self.cache.set(f"key_{i}", f"value_{i}")

        # Fazer alguns hits e misses
        for i in range(5):
            self.cache.get(f"key_{i}")  # Hit

        for i in range(10, 15):
            self.cache.get(f"key_{i}")  # Miss

        stats = self.cache.get_stats()

        assert stats['hits'] == 5
        assert stats['misses'] == 5
        assert stats['hit_rate'] == 50.0
        assert stats['size'] == 10


class TestSerializationPerformance:
    """Testes de performance de serialização."""

    def test_orjson_vs_json(self):
        """Compara performance de orjson vs json padrão."""
        import json
        import orjson

        # Dados de teste
        data = {
            "id": 1,
            "nome": "Teste",
            "items": [{"id": i, "value": f"item_{i}"} for i in range(100)]
        }

        # Benchmark json
        start = time.time()
        for _ in range(1000):
            json.dumps(data)
        json_elapsed = time.time() - start

        # Benchmark orjson
        start = time.time()
        for _ in range(1000):
            orjson.dumps(data)
        orjson_elapsed = time.time() - start

        # orjson deve ser pelo menos 1.5x mais rápido
        speedup = json_elapsed / orjson_elapsed
        assert speedup >= 1.5, f"orjson apenas {speedup:.2f}x mais rápido"


class TestEndToEndPerformance:
    """Testes de performance end-to-end."""

    def test_voting_flow_performance(self):
        """Testa performance do fluxo completo de votação."""
        from core.processors.classes import SistemaVotacao
        from core.models.classes import Candidato, Partido, Cargo, Eleicao
        import tempfile
        import os

        # Criar chaves temporárias
        with tempfile.TemporaryDirectory() as tmpdir:
            # Gerar chaves
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.primitives import serialization
            from cryptography.fernet import Fernet

            private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            private_key_path = os.path.join(tmpdir, "private_key.pem")
            with open(private_key_path, "wb") as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))

            crypto_key = Fernet.generate_key()
            crypto_key_path = os.path.join(tmpdir, "crypto_key.pem")
            with open(crypto_key_path, "wb") as f:
                f.write(crypto_key)

            # Inicializar sistema
            sistema = SistemaVotacao(private_key_path, crypto_key_path)

            # Criar candidato
            eleicao = Eleicao(id=1, nome="Eleição Teste", ano=2024)
            partido = Partido(numero=13, nome="Partido Teste", sigla="PT")
            cargo = Cargo(id=1, nome="Prefeito", eleicao=1)
            candidato = Candidato(
                id=1,
                nome="Candidato Teste",
                codigo="13",
                partido=partido,
                cargo=cargo,
                eleicao=eleicao
            )

            # Benchmark: 100 votos
            start = time.time()
            for i in range(100):
                sistema.votar(candidato)
            elapsed = time.time() - start

            # Verificar performance
            votos_por_segundo = 100 / elapsed
            assert votos_por_segundo > 50, f"Apenas {votos_por_segundo:.2f} votos/s"

            # Verificar blockchain
            assert len(sistema.blockchain.chain) == 101  # 100 + genesis


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
