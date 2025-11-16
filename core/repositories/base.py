"""
Repositório base para operações com Redis.
"""
import gzip
import json
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

import redis
from loguru import logger


class BaseRepository(ABC):
    """
    Classe base para repositórios com Redis.
    Implementa operações CRUD básicas e funcionalidades de compressão.
    """

    # Threshold de compressão: dados maiores que 1KB serão comprimidos
    COMPRESSION_THRESHOLD = 1024

    def __init__(self, redis_client: redis.Redis, prefix: str):
        """
        Inicializa o repositório.

        :param redis_client: Cliente Redis configurado
        :param prefix: Prefixo para as chaves no Redis (ex: 'candidato', 'cargo')
        """
        self.redis_client = redis_client
        self.prefix = prefix

    def _get_key(self, id: Any) -> str:
        """
        Gera a chave completa para o Redis.

        :param id: Identificador do objeto
        :return: Chave formatada com prefixo
        """
        return f"{self.prefix}:{id}"

    def _get_index_key(self, field: str) -> str:
        """
        Gera chave para índices secundários.

        :param field: Nome do campo indexado
        :return: Chave do índice
        """
        return f"{self.prefix}:index:{field}"

    def _compress_data(self, data: str) -> bytes:
        """
        Comprime dados se excederem o threshold.

        :param data: Dados em string para comprimir
        :return: Dados comprimidos ou originais
        """
        data_bytes = data.encode('utf-8')
        if len(data_bytes) > self.COMPRESSION_THRESHOLD:
            compressed = gzip.compress(data_bytes)
            logger.debug(f"Comprimido: {len(data_bytes)} -> {len(compressed)} bytes")
            return b'GZIP:' + compressed
        return data_bytes

    def _decompress_data(self, data: bytes) -> str:
        """
        Descomprime dados se necessário.

        :param data: Dados (possivelmente comprimidos)
        :return: Dados descomprimidos como string
        """
        if data.startswith(b'GZIP:'):
            decompressed = gzip.decompress(data[5:])
            return decompressed.decode('utf-8')
        return data.decode('utf-8')

    def get(self, id: Any) -> Optional[Dict[str, Any]]:
        """
        Busca um objeto por ID.

        :param id: Identificador do objeto
        :return: Dicionário com os dados ou None
        """
        try:
            key = self._get_key(id)
            data = self.redis_client.get(key)
            if data:
                decompressed = self._decompress_data(data)
                return json.loads(decompressed)
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar {self.prefix}:{id} - {str(e)}")
            return None

    def get_all(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Busca todos os objetos do tipo.

        :param limit: Limite máximo de resultados (padrão: 1000)
        :return: Lista de objetos
        """
        try:
            pattern = f"{self.prefix}:*"
            keys = []
            # Usar scan para evitar bloqueio do Redis
            for key in self.redis_client.scan_iter(match=pattern, count=100):
                # Ignorar chaves de índice
                if ':index:' not in key:
                    keys.append(key)
                if len(keys) >= limit:
                    break

            results = []
            for key in keys:
                data = self.redis_client.get(key)
                if data:
                    decompressed = self._decompress_data(data)
                    results.append(json.loads(decompressed))

            return results
        except Exception as e:
            logger.error(f"Erro ao buscar todos {self.prefix} - {str(e)}")
            return []

    def save(self, id: Any, data: Dict[str, Any]) -> bool:
        """
        Salva um objeto no Redis.

        :param id: Identificador do objeto
        :param data: Dados a serem salvos
        :return: True se salvou com sucesso
        """
        try:
            key = self._get_key(id)
            json_data = json.dumps(data, ensure_ascii=False)
            compressed = self._compress_data(json_data)
            self.redis_client.set(key, compressed)
            logger.debug(f"Salvo {self.prefix}:{id}")
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar {self.prefix}:{id} - {str(e)}")
            return False

    def delete(self, id: Any) -> bool:
        """
        Remove um objeto do Redis.

        :param id: Identificador do objeto
        :return: True se removeu com sucesso
        """
        try:
            key = self._get_key(id)
            result = self.redis_client.delete(key)
            logger.debug(f"Removido {self.prefix}:{id}")
            return result > 0
        except Exception as e:
            logger.error(f"Erro ao remover {self.prefix}:{id} - {str(e)}")
            return False

    def exists(self, id: Any) -> bool:
        """
        Verifica se um objeto existe.

        :param id: Identificador do objeto
        :return: True se existe
        """
        try:
            key = self._get_key(id)
            return self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Erro ao verificar existência {self.prefix}:{id} - {str(e)}")
            return False

    def count(self) -> int:
        """
        Conta quantos objetos existem.

        :return: Número de objetos
        """
        try:
            pattern = f"{self.prefix}:*"
            count = 0
            for _ in self.redis_client.scan_iter(match=pattern, count=100):
                if ':index:' not in _:
                    count += 1
            return count
        except Exception as e:
            logger.error(f"Erro ao contar {self.prefix} - {str(e)}")
            return 0

    def get_paginated(self, skip: int = 0, limit: int = 10) -> Dict[str, Any]:
        """
        Busca objetos com paginação.

        :param skip: Número de registros a pular
        :param limit: Número máximo de registros a retornar
        :return: Dicionário com dados paginados e metadados
        """
        try:
            all_items = self.get_all(limit=skip + limit + 100)
            total = len(all_items)
            items = all_items[skip:skip + limit]

            return {
                "items": items,
                "total": total,
                "skip": skip,
                "limit": limit,
                "page": (skip // limit) + 1 if limit > 0 else 1,
                "pages": (total + limit - 1) // limit if limit > 0 else 1
            }
        except Exception as e:
            logger.error(f"Erro ao buscar paginado {self.prefix} - {str(e)}")
            return {
                "items": [],
                "total": 0,
                "skip": skip,
                "limit": limit,
                "page": 1,
                "pages": 0
            }
