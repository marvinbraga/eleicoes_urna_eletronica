# coding=utf-8
"""
Vote Controller
Marcus Vinicius Braga, 2021.
"""
from utils.controllers.abstract import AbstractController


class VoteController(AbstractController):
    """ Vote Controller """

    def __init__(self, vote, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        self._vote = vote

    def execute(self):
        """ Executa o processamento do voto. """
        return self
