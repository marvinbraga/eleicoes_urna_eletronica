"""
Repositório para gerenciar dados de Votos no Redis.
"""
from typing import List, Dict, Any

from loguru import logger

from .base import BaseRepository


class VotoRepository(BaseRepository):
    """
    Repositório específico para Votos.
    """

    def __init__(self, redis_client):
        super().__init__(redis_client, prefix="votos")

    def add_voto(self, eleicao_id: int, voto_data: str) -> bool:
        """
        Adiciona um voto à lista de votos da eleição.

        :param eleicao_id: ID da eleição
        :param voto_data: Dados do voto em JSON
        :return: True se adicionou com sucesso
        """
        try:
            key = self._get_key(eleicao_id)
            compressed = self._compress_data(voto_data)
            self.redis_client.rpush(key, compressed)
            logger.debug(f"Voto adicionado à eleição {eleicao_id}")
            return True
        except Exception as e:
            logger.error(f"Erro ao adicionar voto - {str(e)}")
            return False

    def get_votos_by_eleicao(self, eleicao_id: int, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """
        Busca votos de uma eleição com paginação.

        :param eleicao_id: ID da eleição
        :param skip: Registros a pular
        :param limit: Limite de registros
        :return: Dicionário com votos paginados
        """
        try:
            import json
            key = self._get_key(eleicao_id)

            # Contar total de votos
            total = self.redis_client.llen(key)

            # Buscar votos paginados
            votos_raw = self.redis_client.lrange(key, skip, skip + limit - 1)
            votos = []
            for voto_raw in votos_raw:
                decompressed = self._decompress_data(voto_raw)
                votos.append(json.loads(decompressed))

            return {
                "items": votos,
                "total": total,
                "skip": skip,
                "limit": limit,
                "page": (skip // limit) + 1 if limit > 0 else 1,
                "pages": (total + limit - 1) // limit if limit > 0 else 1
            }
        except Exception as e:
            logger.error(f"Erro ao buscar votos da eleição {eleicao_id} - {str(e)}")
            return {
                "items": [],
                "total": 0,
                "skip": skip,
                "limit": limit,
                "page": 1,
                "pages": 0
            }

    def count_votos(self, eleicao_id: int) -> int:
        """
        Conta o número de votos de uma eleição.

        :param eleicao_id: ID da eleição
        :return: Número de votos
        """
        try:
            key = self._get_key(eleicao_id)
            return self.redis_client.llen(key)
        except Exception as e:
            logger.error(f"Erro ao contar votos da eleição {eleicao_id} - {str(e)}")
            return 0
