"""
Módulo de repositórios para acesso a dados no Redis.
"""
from .base import BaseRepository
from .candidato_repository import CandidatoRepository
from .cargo_repository import CargoRepository
from .eleicao_repository import EleicaoRepository
from .voto_repository import VotoRepository

__all__ = [
    'BaseRepository',
    'CandidatoRepository',
    'CargoRepository',
    'EleicaoRepository',
    'VotoRepository',
]
