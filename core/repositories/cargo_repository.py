"""
Repositório para gerenciar dados de Cargos no Redis.
"""
from typing import List, Dict, Any

from loguru import logger

from .base import BaseRepository


class CargoRepository(BaseRepository):
    """
    Repositório específico para Cargos.
    """

    def __init__(self, redis_client):
        super().__init__(redis_client, prefix="cargo")

    def get_by_eleicao(self, eleicao_id: int, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """
        Busca cargos por eleição com paginação.

        :param eleicao_id: ID da eleição
        :param skip: Registros a pular
        :param limit: Limite de registros
        :return: Dicionário com cargos paginados
        """
        try:
            # Buscar do índice secundário
            index_key = f"{self.prefix}:index:eleicao:{eleicao_id}"
            cargo_ids = self.redis_client.smembers(index_key)

            if cargo_ids:
                # Usar índice se disponível
                cargos = []
                for cargo_id in cargo_ids:
                    cargo = self.get(cargo_id.decode('utf-8') if isinstance(cargo_id, bytes) else cargo_id)
                    if cargo:
                        cargos.append(cargo)
            else:
                # Fallback: buscar todos e filtrar
                all_cargos = self.get_all(limit=1000)
                cargos = [c for c in all_cargos if c.get('eleicao') == eleicao_id]

            total = len(cargos)
            items = cargos[skip:skip + limit]

            return {
                "items": items,
                "total": total,
                "skip": skip,
                "limit": limit,
                "page": (skip // limit) + 1 if limit > 0 else 1,
                "pages": (total + limit - 1) // limit if limit > 0 else 1
            }
        except Exception as e:
            logger.error(f"Erro ao buscar cargos por eleição {eleicao_id} - {str(e)}")
            return {
                "items": [],
                "total": 0,
                "skip": skip,
                "limit": limit,
                "page": 1,
                "pages": 0
            }

    def save_with_index(self, cargo_id: Any, data: Dict[str, Any]) -> bool:
        """
        Salva cargo e atualiza índice secundário.

        :param cargo_id: ID do cargo
        :param data: Dados do cargo
        :return: True se salvou com sucesso
        """
        if self.save(cargo_id, data):
            # Atualizar índice por eleicao_id
            if 'eleicao' in data:
                index_key = f"{self.prefix}:index:eleicao:{data['eleicao']}"
                self.redis_client.sadd(index_key, str(cargo_id))
            return True
        return False
