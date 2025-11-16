"""
Sistema de cache em memória para otimizar consultas frequentes.
"""
import functools
import time
from typing import Callable, Any, Optional

from cachetools import TTLCache
from loguru import logger


class CacheManager:
    """
    Gerenciador de cache centralizado usando TTL Cache.
    """

    def __init__(self, maxsize: int = 1000, ttl: int = 300):
        """
        Inicializa o gerenciador de cache.

        :param maxsize: Tamanho máximo do cache
        :param ttl: Time-to-live em segundos (padrão: 5 minutos)
        """
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }

    def get(self, key: str) -> Optional[Any]:
        """
        Busca valor no cache.

        :param key: Chave do cache
        :return: Valor cacheado ou None
        """
        try:
            value = self.cache[key]
            self.stats['hits'] += 1
            logger.debug(f"Cache HIT: {key}")
            return value
        except KeyError:
            self.stats['misses'] += 1
            logger.debug(f"Cache MISS: {key}")
            return None

    def set(self, key: str, value: Any) -> None:
        """
        Armazena valor no cache.

        :param key: Chave do cache
        :param value: Valor a ser cacheado
        """
        try:
            self.cache[key] = value
            logger.debug(f"Cache SET: {key}")
        except Exception as e:
            logger.error(f"Erro ao armazenar no cache: {str(e)}")

    def delete(self, key: str) -> None:
        """
        Remove valor do cache.

        :param key: Chave do cache
        """
        try:
            if key in self.cache:
                del self.cache[key]
                logger.debug(f"Cache DELETE: {key}")
        except Exception as e:
            logger.error(f"Erro ao remover do cache: {str(e)}")

    def clear(self) -> None:
        """
        Limpa todo o cache.
        """
        self.cache.clear()
        logger.info("Cache limpo")

    def invalidate_pattern(self, pattern: str) -> None:
        """
        Invalida chaves que correspondem a um padrão.

        :param pattern: Padrão para buscar chaves (ex: 'candidatos:*')
        """
        keys_to_delete = [key for key in self.cache.keys() if pattern in key]
        for key in keys_to_delete:
            self.delete(key)
        logger.info(f"Invalidadas {len(keys_to_delete)} chaves com padrão '{pattern}'")

    def get_stats(self) -> dict:
        """
        Retorna estatísticas do cache.

        :return: Dicionário com estatísticas
        """
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0

        return {
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'hit_rate': round(hit_rate, 2),
            'size': len(self.cache),
            'maxsize': self.cache.maxsize
        }


# Instância global do cache manager
cache_manager = CacheManager(maxsize=1000, ttl=300)


def cached(key_prefix: str = "", ttl: Optional[int] = None):
    """
    Decorator para cachear resultados de funções.

    :param key_prefix: Prefixo para a chave do cache
    :param ttl: Time-to-live personalizado (opcional)
    :return: Decorator
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Gerar chave do cache baseada nos argumentos
            cache_key = f"{key_prefix}:{func.__name__}:{args}:{kwargs}"

            # Tentar buscar do cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Executar função
            result = func(*args, **kwargs)

            # Armazenar no cache
            cache_manager.set(cache_key, result)

            return result
        return wrapper
    return decorator


def invalidate_cache(pattern: str):
    """
    Invalida cache baseado em padrão.

    :param pattern: Padrão para buscar chaves
    """
    cache_manager.invalidate_pattern(pattern)


def clear_cache():
    """
    Limpa todo o cache.
    """
    cache_manager.clear()


def get_cache_stats() -> dict:
    """
    Retorna estatísticas do cache.

    :return: Dicionário com estatísticas
    """
    return cache_manager.get_stats()
