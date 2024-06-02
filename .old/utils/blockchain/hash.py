# coding=utf-8
"""
Hash Module.
"""
import hashlib


class ConferenceIdGen:
    """ Class to generate conference id do models. """

    def __init__(self, value):
        self._value = value

    def execute(self):
        """ Generate Id with hashes. """
        h = hashlib.blake2b(digest_size=8)
        h.update(str(self._value).encode())
        return str(h.hexdigest())
