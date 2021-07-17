# coding=utf-8
"""
Ballot Box Model Module.
Marcus Vinicius Braga, 2021.
"""
from utils.models.abstracts import AbstractDictSerializer
from utils.models.bases import Model


class BallotBoxModelDictSerializer(AbstractDictSerializer):
    """ Classe para serializar um Model para Dict.  """

    def __init__(self, model):
        self._model = model

    def as_dict(self):
        """ Converte Model para Dict """
        result = self._model.__dict__.copy()
        self._model.pop_attr(result, '_election', self._model.election)
        votes = []
        for vote in self._model.votes:
            votes.append(vote.as_dict())
        result.pop('_votes')
        result['_votes'] = votes
        return result


class BallotBoxModel(Model):
    """ Classe Model de Urna Eletrônica Eleitoral. """

    def __init__(self, code, election, candidates):
        super().__init__(code, election, candidates)
        self._candidates = candidates
        self._code = code
        self._election = election
        self._votes = []

    @property
    def votes(self):
        """ Property Votes. """
        return self._votes

    @property
    def election(self):
        """ Property Election. """
        return self._election

    def pop_attr(self, dct, name, obj):
        """ Expõe o método protegido. """
        return self._pop_attr(dct, name, obj)

    def as_dict(self):
        """ Serialize to JSon. """
        return BallotBoxModelDictSerializer(self).as_dict()

    def add_vote(self, vote):
        """ Adiciona um voto à urna. """
        self._votes.append(vote)
        return self
