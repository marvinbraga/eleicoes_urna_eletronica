# coding=utf-8
"""
Ballot Box Model Module.
Marcus Vinicius Braga, 2021.
"""
from utils.blockchain.manager import BlockchainManager
from utils.models.bases import Model


class BallotBoxModel(Model):
    """ Classe Model de Urna Eletrônica Eleitoral. """
    def __init__(self, code, election, candidates):
        super().__init__(code, election, candidates)
        self._blockchain = BlockchainManager()
        self._candidates = candidates
        self._code = code
        self._election = election
        self._votes = []

    @property
    def votes(self):
        """ Property Votes. """
        return self._votes

    def as_dict(self):
        """ Serialize to JSon. """
        result = self.__dict__.copy()
        result.pop('_blockchain')
        self._pop_attr(result, '_election', self._election)
        votes = []
        for vote in self._votes:
            votes.append(vote.as_dict())
        result.pop('_votes')
        result['_votes'] = votes
        return result

    def add_vote(self, vote):
        """ Adiciona um voto à urna. """
        self._votes.append(vote)
        self._blockchain.add_transactions(vote.data)
        return self
