"""
Repositório para gerenciar dados de Candidatos no Redis.
"""
from typing import List, Dict, Any

from loguru import logger

from .base import BaseRepository


class CandidatoRepository(BaseRepository):
    """
    Repositório específico para Candidatos.
    """

    def __init__(self, redis_client):
        super().__init__(redis_client, prefix="candidato")

    def get_by_cargo(self, cargo_id: int, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """
        Busca candidatos por cargo com paginação.

        :param cargo_id: ID do cargo
        :param skip: Registros a pular
        :param limit: Limite de registros
        :return: Dicionário com candidatos paginados
        """
        try:
            # Buscar do índice secundário
            index_key = f"{self.prefix}:index:cargo:{cargo_id}"
            candidato_ids = self.redis_client.smembers(index_key)

            if candidato_ids:
                # Usar índice se disponível
                candidatos = []
                for candidato_id in candidato_ids:
                    candidato = self.get(
                        candidato_id.decode('utf-8') if isinstance(candidato_id, bytes) else candidato_id
                    )
                    if candidato:
                        candidatos.append(candidato)
            else:
                # Fallback: buscar todos e filtrar
                all_candidatos = self.get_all(limit=1000)
                candidatos = [c for c in all_candidatos if c.get('cargo', {}).get('id') == cargo_id]

            total = len(candidatos)
            items = candidatos[skip:skip + limit]

            return {
                "items": items,
                "total": total,
                "skip": skip,
                "limit": limit,
                "page": (skip // limit) + 1 if limit > 0 else 1,
                "pages": (total + limit - 1) // limit if limit > 0 else 1
            }
        except Exception as e:
            logger.error(f"Erro ao buscar candidatos por cargo {cargo_id} - {str(e)}")
            return {
                "items": [],
                "total": 0,
                "skip": skip,
                "limit": limit,
                "page": 1,
                "pages": 0
            }

    def get_by_codigo(self, cargo_id: int, codigo: str) -> List[Dict[str, Any]]:
        """
        Busca candidatos por código (busca por prefixo).

        :param cargo_id: ID do cargo
        :param codigo: Código do candidato (ou parte dele)
        :return: Lista de candidatos que começam com o código
        """
        try:
            # Buscar do índice por código
            index_key = f"{self.prefix}:index:codigo:{codigo}"
            candidato_ids = self.redis_client.smembers(index_key)

            candidatos = []
            if candidato_ids:
                # Usar índice se disponível
                for candidato_id in candidato_ids:
                    candidato = self.get(
                        candidato_id.decode('utf-8') if isinstance(candidato_id, bytes) else candidato_id
                    )
                    if candidato and candidato.get('cargo', {}).get('id') == cargo_id:
                        candidatos.append(candidato)
            else:
                # Fallback: buscar por cargo e filtrar
                result = self.get_by_cargo(cargo_id, limit=1000)
                for candidato in result.get('items', []):
                    if candidato.get('codigo', '').startswith(codigo):
                        candidatos.append(candidato)

            return candidatos
        except Exception as e:
            logger.error(f"Erro ao buscar candidatos por código {codigo} - {str(e)}")
            return []

    def save_with_index(self, candidato_id: Any, data: Dict[str, Any]) -> bool:
        """
        Salva candidato e atualiza índices secundários.

        :param candidato_id: ID do candidato
        :param data: Dados do candidato
        :return: True se salvou com sucesso
        """
        if self.save(candidato_id, data):
            # Atualizar índice por cargo_id
            cargo_id = data.get('cargo', {}).get('id')
            if cargo_id:
                index_key = f"{self.prefix}:index:cargo:{cargo_id}"
                self.redis_client.sadd(index_key, str(candidato_id))

            # Atualizar índice por código (para cada prefixo)
            codigo = data.get('codigo', '')
            if codigo:
                # Criar índices para todos os prefixos do código
                for i in range(1, len(codigo) + 1):
                    prefix = codigo[:i]
                    index_key = f"{self.prefix}:index:codigo:{prefix}"
                    self.redis_client.sadd(index_key, str(candidato_id))

            return True
        return False
