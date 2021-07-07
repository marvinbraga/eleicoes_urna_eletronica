# coding=utf-8
"""
Blockchain Manager Module
Marcus Vinicius Braga, 2021.
"""
from datetime import datetime

from utils import settings
from utils.blockchain.block import Block
from utils.patterns.singleton_meta import Singleton


class BlockchainManager(metaclass=Singleton):
    """ Class to manager blockchain data. """

    def __init__(self):
        self._blocks = []
        self._transactions = []
        self._start_date = datetime.now()
        self._end_date = None

    @property
    def blocks(self):
        """
        This method returns the Blocks field.
        :return: Blocks list.
        """
        return self._blocks

    @property
    def order(self):
        """
        This method returns the transactions count plus one.
        :return: New count.
        """
        return len(self._transactions) + 1

    def add_transactions(self, transactions):
        """
        This method adds transactions to blocks.
        """
        self._blocks.append(Block(self._get_old_hash(), transactions).hash)
        self._transactions.append(transactions)
        if settings.DEBUG:
            self._print_results()
        return self

    def _start_genesis(self):
        """
        This method creates the first block with the first transactions.
        """
        self.add_transactions(['0', settings.DEFAULT_START_TRANSACTION, settings.DEFAULT_START_HASH])
        return self

    def _get_old_hash(self):
        """
        This method takes the last hash value saved in the blocks.
        :return: Old hash string.
        """
        old_hash = self._blocks[len(self._blocks) - 1] if len(self._blocks) > 0 else settings.DEFAULT_START_HASH
        return old_hash

    def _print_results(self):
        """
        This method just prints the information.
        """
        print(self._transactions)
        print(self._blocks)
        return self
