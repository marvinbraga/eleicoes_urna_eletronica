# coding=utf-8
"""
Ballot Boxes Controller Module
Marcus Vinicius Braga, 2021.
"""
import os

from utils.controllers.abstract import AbstractController


class BallotBoxesController(AbstractController):
    """ Controller """
    def __init__(self, model, *args, **kwargs):
        self._kwargs = kwargs
        self._args = args
        self._blockchain = self._kwargs.get('blockchain')
        self._model = model

    @property
    def model(self):
        """ Return model """
        return self._model

    def execute(self):
        """ Executa o processo para urna eletrônica. """
        self._save()
        return self

    def add_vote(self, vote):
        """ Adiciona um novo voto. """
        self._model.add_vote(vote)
        if self._blockchain:
            self._blockchain.add_transactions(vote.data)
            vote.set_hash(self._blockchain.last_block())
        vote.save()
        return self

    def _save(self):
        """ Save model. """
        if os.path.isfile(self._model.__dict__.get('_filename')):
            os.remove(self._model.__dict__.get('_filename'))
        self._model.save()
        return self
