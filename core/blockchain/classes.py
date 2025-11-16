from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Optional, List, Dict, Any


class Block:
    """
    Representa um bloco na blockchain.
    """
    def __init__(
        self,
        index: int,
        timestamp: datetime,
        transactions: List[Any],
        previous_hash: str
    ) -> None:
        """
        Inicializa um novo bloco.

        :param index: Índice do bloco na cadeia.
        :param timestamp: Timestamp de criação do bloco.
        :param transactions: Lista de transações incluídas no bloco.
        :param previous_hash: Hash do bloco anterior.
        """
        self.index: int = index
        self.timestamp: datetime = timestamp
        self.transactions: List[Any] = transactions
        self.previous_hash: str = previous_hash
        self.hash: str = self.calculate_hash()
        # Lazy loading: transações são carregadas sob demanda
        self._transactions_loaded: bool = True

    def calculate_hash(self) -> str:
        """
        Calcula o hash SHA-256 do bloco.

        :return: Hash do bloco como string hexadecimal.
        """
        data_string = json.dumps(self.transactions, sort_keys=True)
        timestamp_str = self.timestamp.isoformat()
        return hashlib.sha256(f"{self.index}{timestamp_str}{data_string}{self.previous_hash}".encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """
        Converte o bloco para dicionário.

        :return: Dicionário com os dados do bloco.
        """
        return {
            'index': self.index,
            'timestamp': self.timestamp.isoformat(),
            'transactions': self.transactions,
            'previous_hash': self.previous_hash,
            'hash': self.hash
        }


class Blockchain:
    """
    Implementação otimizada da Blockchain com índices e cache.
    """
    def __init__(self) -> None:
        """
        Inicializa a blockchain com o bloco genesis.
        """
        self.chain: List[Block] = [self.create_genesis_block()]
        self.pending_transactions: List[Any] = []
        # Índice de hash para busca rápida O(1)
        self._hash_index: Dict[str, Block] = {}
        # Cache de blocos para acesso rápido
        self._block_cache: Dict[int, Block] = {}
        # Inicializar índices
        self._rebuild_indexes()

    def create_genesis_block(self) -> Block:
        """
        Cria o bloco gênesis (primeiro bloco da cadeia).

        :return: Bloco genesis.
        """
        return Block(0, datetime.now(), [], "0")

    def add_block(self, transactions: List[Any]) -> None:
        """
        Adiciona um novo bloco à cadeia.

        :param transactions: Lista de transações a serem incluídas no bloco.
        """
        previous_block = self.chain[-1]
        new_block = Block(
            len(self.chain),
            datetime.now(),
            transactions,
            previous_block.hash
        )
        self.chain.append(new_block)
        # Atualizar índices
        self._add_to_index(new_block)

    def add_transaction(self, transaction: Any) -> None:
        """
        Adiciona uma transação à lista de transações pendentes.

        :param transaction: Transação a ser adicionada.
        """
        self.pending_transactions.append(transaction)

    def mine_pending_transactions(self) -> None:
        """
        Minera as transações pendentes criando um novo bloco.
        """
        if len(self.pending_transactions) > 0:
            self.add_block(self.pending_transactions)
            self.pending_transactions = []

    def get_block_by_index(self, index: int) -> Optional[Block]:
        """
        Busca um bloco por índice com cache.

        :param index: Índice do bloco.
        :return: Bloco ou None se o índice for inválido.
        """
        # Verificar cache primeiro
        if index in self._block_cache:
            return self._block_cache[index]

        # Buscar na cadeia
        if 0 <= index < len(self.chain):
            block = self.chain[index]
            # Adicionar ao cache
            self._block_cache[index] = block
            return block
        return None

    def get_block_by_hash(self, block_hash: str) -> Optional[Block]:
        """
        Busca um bloco por hash usando índice otimizado O(1).

        :param block_hash: Hash do bloco.
        :return: Bloco ou None se não encontrado.
        """
        return self._hash_index.get(block_hash)

    def _add_to_index(self, block: Block) -> None:
        """
        Adiciona bloco aos índices.

        :param block: Bloco a ser indexado.
        """
        self._hash_index[block.hash] = block
        self._block_cache[block.index] = block

    def _rebuild_indexes(self) -> None:
        """
        Reconstrói os índices a partir da cadeia existente.
        """
        self._hash_index.clear()
        self._block_cache.clear()
        for block in self.chain:
            self._add_to_index(block)

    def is_chain_valid(self) -> bool:
        """
        Valida a integridade da blockchain.

        :return: True se a blockchain for válida, False caso contrário.
        """
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            if current_block.hash != current_block.calculate_hash():
                return False
            if current_block.previous_hash != previous_block.hash:
                return False
        return True

    def is_empty(self) -> bool:
        """
        Verifica se a blockchain está vazia (contém apenas o bloco genesis).

        :return: True se a blockchain contém apenas o bloco genesis, False caso contrário.
        """
        return len(self.chain) <= 1

    def get_last_block(self) -> Block:
        """
        Retorna o último bloco da blockchain.

        :return: O último bloco da blockchain.
        :raises: ValueError se a blockchain estiver vazia.
        """
        if len(self.chain) == 0:
            raise ValueError("Blockchain está vazia")
        return self.chain[-1]

    def get_chain_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas da blockchain.

        :return: Dicionário com estatísticas da blockchain.
        """
        return {
            'total_blocks': len(self.chain),
            'pending_transactions': len(self.pending_transactions),
            'last_block_hash': self.chain[-1].hash if self.chain else None,
            'cache_size': len(self._block_cache),
            'index_size': len(self._hash_index)
        }
