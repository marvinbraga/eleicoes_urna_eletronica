# coding=utf-8
"""
Blockchain Module
Marcus Vinicius Braga, 2021.
"""
import hashlib

from utils import settings


class Block:
    """ Class to implement Blockchain strategy. """

    def __init__(self, hash_str, transactions):
        self._old_hash = hash_str
        self._transactions = transactions
        self._hash = self._convert_to_hash(settings.DEFAULT_START_HASH)
        self._convert_transactions()

    def __str__(self):
        return self.hash

    @property
    def hash(self):
        """
        This method returns the information of the new hash calculated for the new block.
        """
        return self._hash

    def _convert_transactions(self):
        """
        This method creates a new hash for the transactions along with the hash from the previous block.
        """
        if len(self._transactions) > 0:
            contents = ["|".join(self._transactions), self._old_hash]
            self._hash = self._convert_to_hash("|".join(contents))

    @staticmethod
    def _convert_to_hash(content_str):
        """
        This method converts string content into a hash.
        :param content_str: Content to convert.
        :return: Hash string.
        """
        return str(hashlib.sha256(content_str.encode()).hexdigest())
