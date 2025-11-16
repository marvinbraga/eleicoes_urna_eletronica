"""
Repositório para gerenciar dados de Eleições no Redis.
"""
from typing import Optional, Dict, Any

from .base import BaseRepository


class EleicaoRepository(BaseRepository):
    """
    Repositório específico para Eleições.
    """

    def __init__(self, redis_client):
        super().__init__(redis_client, prefix="eleicao")

    def get_by_id(self, eleicao_id: int) -> Optional[Dict[str, Any]]:
        """
        Busca uma eleição por ID.

        :param eleicao_id: ID da eleição
        :return: Dados da eleição ou None
        """
        return self.get(eleicao_id)
